"""PyQt6 GUI: 원고 선택 + 제목 입력 → 인용 검토 → PPT 생성."""
from __future__ import annotations

import sys
import subprocess
import traceback
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QMessageBox, QDialog, QDialogButtonBox, QListWidget,
    QComboBox, QSpinBox,
)

from bible_books import BOOKS
from extractor import Reference
from service import extract_refs, fetch_and_build, __version__


# ---------- 다이얼로그 ----------

class AddReferenceDialog(QDialog):
    """삽입 위치 + 책/장/절 직접 입력."""

    def __init__(self, current_count: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("성구 추가")
        self.resize(440, 260)

        form = QFormLayout(self)

        self.position = QSpinBox()
        self.position.setRange(1, current_count + 1)
        self.position.setValue(current_count + 1)  # 기본: 맨 뒤

        self.book = QComboBox()
        for en, ko, _, _ in BOOKS:
            self.book.addItem(f"{ko} ({en})", (en, ko))

        self.chapter = QSpinBox()
        self.chapter.setRange(1, 150)

        self.verse_start = QSpinBox()
        self.verse_start.setRange(1, 176)

        self.verse_end = QSpinBox()
        self.verse_end.setRange(1, 176)
        self.verse_end.setValue(1)

        form.addRow("삽입 위치 (순번):", self.position)
        form.addRow("책:", self.book)
        form.addRow("장:", self.chapter)
        form.addRow("시작 절:", self.verse_start)
        form.addRow("끝 절:", self.verse_end)

        # 시작 절 바뀌면 끝 절 최소값도 같이 끌어올림
        self.verse_start.valueChanged.connect(self._sync_verse_end)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("추가")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("취소")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _sync_verse_end(self, vs_value: int):
        if self.verse_end.value() < vs_value:
            self.verse_end.setValue(vs_value)

    def reference(self) -> Reference:
        en, ko = self.book.currentData()
        vs = self.verse_start.value()
        ve = max(self.verse_end.value(), vs)
        return Reference(en, ko, self.chapter.value(), vs, ve)

    def position_index(self) -> int:
        return self.position.value() - 1


class ReviewDialog(QDialog):
    """추출된 인용 리스트 검토 + 수동 추가/삭제/순서 변경."""

    def __init__(self, refs: list[Reference], parent=None):
        super().__init__(parent)
        self.setWindowTitle("성구 인용 검토")
        self.resize(620, 500)
        self._refs: list[Reference] = list(refs)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            "원고에서 자동 추출된 인용 목록입니다.\n"
            "누락된 구절은 [추가]로 직접 넣고, [위/아래]로 슬라이드 순서를 맞춘 뒤 [생성]을 눌러주세요."
        ))

        self.list_widget = QListWidget()
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.list_widget.setFont(mono)
        self.list_widget.itemDoubleClicked.connect(self._on_edit)
        layout.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("추가")
        self.remove_btn = QPushButton("삭제")
        self.up_btn = QPushButton("위로")
        self.down_btn = QPushButton("아래로")
        for b in (self.add_btn, self.remove_btn, self.up_btn, self.down_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
        self.up_btn.clicked.connect(lambda: self._move(-1))
        self.down_btn.clicked.connect(lambda: self._move(+1))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok,
            parent=self,
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText("생성")
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("취소")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh()

    def _refresh(self):
        self.list_widget.clear()
        for i, r in enumerate(self._refs, 1):
            n_verses = r.verse_end - r.verse_start + 1
            self.list_widget.addItem(
                f"{i:2d}. {r.header_en:<24s} |  {r.header_ko:<22s} ({n_verses}절)"
            )

    def _on_add(self):
        dlg = AddReferenceDialog(len(self._refs), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            pos = dlg.position_index()
            self._refs.insert(pos, dlg.reference())
            self._refresh()
            self.list_widget.setCurrentRow(pos)

    def _on_edit(self, _item):
        # 더블클릭 시 편집은 미지원 — 삭제 후 다시 추가 안내
        row = self.list_widget.currentRow()
        if not (0 <= row < len(self._refs)):
            return
        QMessageBox.information(
            self, "편집",
            "편집은 [삭제] 후 [추가]로 다시 입력해 주세요.",
        )

    def _on_remove(self):
        row = self.list_widget.currentRow()
        if not (0 <= row < len(self._refs)):
            return
        del self._refs[row]
        self._refresh()
        # 삭제 후 선택 유지
        new_row = min(row, len(self._refs) - 1)
        if new_row >= 0:
            self.list_widget.setCurrentRow(new_row)

    def _move(self, delta: int):
        row = self.list_widget.currentRow()
        new_row = row + delta
        if not (0 <= row < len(self._refs)) or not (0 <= new_row < len(self._refs)):
            return
        self._refs[row], self._refs[new_row] = self._refs[new_row], self._refs[row]
        self._refresh()
        self.list_widget.setCurrentRow(new_row)

    def references(self) -> list[Reference]:
        return list(self._refs)


# ---------- 백그라운드 워커 ----------

class Worker(QThread):
    log = pyqtSignal(str)
    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, refs: list[Reference], output: str,
                 title_en: str, title_ko: str, main_passage: str):
        super().__init__()
        self.refs = refs
        self.output = output
        self.title_en = title_en
        self.title_ko = title_ko
        self.main_passage = main_passage

    def run(self):
        try:
            fetch_and_build(
                refs=self.refs,
                output_path=self.output,
                title_en=self.title_en or None,
                title_ko=self.title_ko or None,
                main_passage=self.main_passage or None,
                log=lambda s: self.log.emit(s),
            )
            self.done.emit(self.output)
        except Exception:
            self.failed.emit(traceback.format_exc())


# ---------- 메인 윈도우 ----------

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"설교 PPT 생성기 v{__version__}")
        self.resize(720, 620)
        self.worker: Worker | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        file_row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.file_edit.setPlaceholderText("설교 원고 파일 (.docx 또는 .txt)")
        browse_btn = QPushButton("파일 선택...")
        browse_btn.clicked.connect(self._on_browse)
        file_row.addWidget(QLabel("원고:"))
        file_row.addWidget(self.file_edit, 1)
        file_row.addWidget(browse_btn)
        root.addLayout(file_row)

        form = QFormLayout()
        self.title_en = QLineEdit()
        self.title_en.setPlaceholderText("예: When Hearts Slowly Drift  (생략하면 타이틀 슬라이드 제외)")
        self.title_ko = QLineEdit()
        self.title_ko.setPlaceholderText("예: 조금씩 하나님에게서 멀어지는 마음")
        self.main_passage = QLineEdit()
        self.main_passage.setPlaceholderText("예: Hebrews 2:1  (생략하면 첫 인용 자동 사용)")
        form.addRow("영문 제목:", self.title_en)
        form.addRow("한글 제목:", self.title_ko)
        form.addRow("타이틀 본문:", self.main_passage)
        root.addLayout(form)

        self.run_btn = QPushButton("PPT 생성")
        self.run_btn.setMinimumHeight(36)
        self.run_btn.clicked.connect(self._on_run)
        root.addWidget(self.run_btn)

        root.addWidget(QLabel("진행 로그:"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.log_view.setFont(mono)
        root.addWidget(self.log_view, 1)

        self.status = QLabel("준비 완료")
        self.status.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self.status)

    # ---------- 핸들러 ----------

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "원고 파일 선택", "",
            "원고 파일 (*.docx *.txt);;모든 파일 (*.*)",
        )
        if path:
            self.file_edit.setText(path)

    def _on_run(self):
        manuscript = self.file_edit.text().strip()
        if not manuscript:
            QMessageBox.warning(self, "원고 없음", "설교 원고 파일을 먼저 선택하세요.")
            return
        manuscript_path = Path(manuscript)
        if not manuscript_path.exists():
            QMessageBox.warning(self, "파일 없음", f"파일을 찾을 수 없습니다:\n{manuscript}")
            return

        output_path = manuscript_path.with_suffix(".pptx")

        # 1. 추출 (메인 스레드, 빠름)
        self.log_view.clear()
        try:
            refs = extract_refs(str(manuscript_path), log=self._append_log)
        except Exception as e:
            QMessageBox.critical(self, "추출 실패", str(e))
            return

        if not refs:
            QMessageBox.information(
                self, "자동 추출 0건",
                "원고에서 자동 추출된 인용이 없습니다.\n검토 화면에서 [추가]로 직접 넣어주세요.",
            )

        # 2. 검토 다이얼로그
        dlg = ReviewDialog(refs, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            self._append_log("[취소] 사용자가 검토 단계에서 취소함")
            self.status.setText("취소됨")
            return

        final_refs = dlg.references()
        if not final_refs:
            QMessageBox.warning(self, "인용 없음", "최소 하나의 성구가 필요합니다.")
            return

        # 3. 덮어쓰기 확인
        if output_path.exists():
            reply = QMessageBox.question(
                self, "덮어쓰기 확인",
                f"이미 같은 이름의 파일이 있습니다:\n{output_path}\n\n덮어쓸까요?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 4. 백그라운드에서 fetch + build
        self.run_btn.setEnabled(False)
        self.status.setText("처리 중...")
        self._append_log("")
        self._append_log(f"[검토 완료] 최종 {len(final_refs)}개 인용")
        for r in final_refs:
            self._append_log(f"  - {r.header_en}  |  {r.header_ko}")

        self.worker = Worker(
            refs=final_refs,
            output=str(output_path),
            title_en=self.title_en.text().strip(),
            title_ko=self.title_ko.text().strip(),
            main_passage=self.main_passage.text().strip(),
        )
        self.worker.log.connect(self._append_log)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _append_log(self, text: str):
        self.log_view.append(text)

    def _on_done(self, output_path: str):
        self._append_log("")
        self._append_log(f"[성공] {output_path}")
        self.status.setText("완료")
        self.run_btn.setEnabled(True)
        reply = QMessageBox.information(
            self, "완료",
            f"PPT가 생성되었습니다:\n{output_path}\n\n파일 위치를 열까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._open_in_explorer(output_path)

    def _on_failed(self, tb_text: str):
        self._append_log("")
        self._append_log("[실패]")
        self._append_log(tb_text)
        self.status.setText("에러")
        self.run_btn.setEnabled(True)
        last = tb_text.strip().splitlines()[-1] if tb_text.strip() else "알 수 없는 에러"
        QMessageBox.critical(self, "에러", last)

    def _open_in_explorer(self, path: str):
        p = Path(path)
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", str(p)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p.parent)])
        except Exception:
            pass


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
