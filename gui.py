"""PyQt6 GUI: 원고 선택 + 제목 입력 → PPT 생성."""
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
    QMessageBox,
)

from service import build_ppt


class Worker(QThread):
    log = pyqtSignal(str)
    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, manuscript: str, output: str,
                 title_en: str, title_ko: str, main_passage: str):
        super().__init__()
        self.manuscript = manuscript
        self.output = output
        self.title_en = title_en
        self.title_ko = title_ko
        self.main_passage = main_passage

    def run(self):
        try:
            build_ppt(
                manuscript_path=self.manuscript,
                output_path=self.output,
                title_en=self.title_en or None,
                title_ko=self.title_ko or None,
                main_passage=self.main_passage or None,
                log=lambda s: self.log.emit(s),
            )
            self.done.emit(self.output)
        except Exception:
            self.failed.emit(traceback.format_exc())


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("설교 PPT 생성기")
        self.resize(720, 620)
        self.worker: Worker | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # 파일 선택 행
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

        # 제목/본문 입력
        form = QFormLayout()
        self.title_en = QLineEdit()
        self.title_en.setPlaceholderText("예: When Hearts Slowly Drift  (생략하면 타이틀 슬라이드 제외)")
        self.title_ko = QLineEdit()
        self.title_ko.setPlaceholderText("예: 조금씩 하나님에게서 멀어지는 마음")
        self.main_passage = QLineEdit()
        self.main_passage.setPlaceholderText("예: Hebrews 2:1  (생략하면 원고의 첫 인용 자동 사용)")
        form.addRow("영문 제목:", self.title_en)
        form.addRow("한글 제목:", self.title_ko)
        form.addRow("타이틀 본문:", self.main_passage)
        root.addLayout(form)

        # 생성 버튼
        self.run_btn = QPushButton("PPT 생성")
        self.run_btn.setMinimumHeight(36)
        self.run_btn.clicked.connect(self._on_run)
        root.addWidget(self.run_btn)

        # 로그
        root.addWidget(QLabel("진행 로그:"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.log_view.setFont(mono)
        root.addWidget(self.log_view, 1)

        # 상태바
        self.status = QLabel("준비 완료")
        self.status.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self.status)

    # ---------- handlers ----------

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

        # 출력: 같은 폴더, 같은 stem, .pptx
        output_path = manuscript_path.with_suffix(".pptx")
        if output_path.exists():
            reply = QMessageBox.question(
                self, "덮어쓰기 확인",
                f"이미 같은 이름의 파일이 있습니다:\n{output_path}\n\n덮어쓸까요?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.log_view.clear()
        self.run_btn.setEnabled(False)
        self.status.setText("처리 중...")

        self.worker = Worker(
            manuscript=str(manuscript_path),
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
        # 마지막 줄(에러 메시지)만 다이얼로그에
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
