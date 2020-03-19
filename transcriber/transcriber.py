from multiprocessing import cpu_count

from transcriber.file_selecter.presenter import FileSelecter
from transcriber.file_selecter.view import FileSelecterView

from transcriber.tag_selecter.presenter import TagSelecter
from transcriber.tag_selecter.view import TagSelecterView
from transcriber.tag_selecter.model import TagSelecterModel

from transcriber.converter.presenter import Converter
from transcriber.converter.view import ConverterView
from transcriber.converter.model import ConverterModel

from PyQt5 import QtWidgets, QtCore


class Transcriber(QtWidgets.QMainWindow):
    def __init__(self):
        super(Transcriber, self).__init__()

        self.file_selecter = FileSelecter(FileSelecterView())
        self.file_selecter.connect_add_clicked(self.load_csv)
        self.file_selecter.connect_del_clicked(self.check_run)

        self.tag_selecter = TagSelecter(TagSelecterView(), TagSelecterModel())
        self.tag_selecter.connect_load_clicked(self.load_tag_file)
        self.tag_selecter.connect_tag_added(self.check_run)
        self.tag_selecter.connect_tag_deleted(self.check_run)

        self.run_widget = Converter(ConverterView(), ConverterModel())
        self.run_widget.connect_run_clicked(self.run_widget.reset_progress)
        self.run_widget.connect_run_clicked(self.convert)
        self.run_widget.connect_conversion_started(self.disable_all)
        self.run_widget.connect_conversion_finished(self.enable_all)
        self.run_widget.connect_conversion_error(print)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.file_selecter.view)
        self.splitter.addWidget(self.tag_selecter.view)

        self._widget_list = QtWidgets.QVBoxLayout()
        self._widget_list.addWidget(self.splitter)
        self._widget_list.addWidget(self.run_widget.view)
        self.setCentralWidget(QtWidgets.QWidget(self))
        self.centralWidget().setLayout(self._widget_list)
        self.setWindowTitle("Transcriber")

    def load_csv(self):
        filenames, _ = QtWidgets.QFileDialog.getOpenFileNames()
        if filenames:
            self.file_selecter.add_files(filenames)
            self.check_run()

    def load_tag_file(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName()
        if filename:
            self.tag_selecter.load_file(filename)
            self.tag_selecter.clear_all()
            self.tag_selecter.clear_new()
            tags = self.tag_selecter.tags
            if tags:
                self.tag_selecter.set_all(tags)
            self.tag_selecter.disable_addition()
            self.tag_selecter.disable_deletion()

    def check_run(self):
        if self.tag_selecter.active_tags and self.file_selecter.filenames:
            self.run_widget.enable_run()
        else:
            self.run_widget.disable_run()

    def convert(self):
        filenames = self.file_selecter.filenames
        tags = self.tag_selecter.active_tags
        total_tags = len(self.tag_selecter.tags)
        self.run_widget.convert(
            filenames,
            tags,
            total_tags,
            cpu_count() if self.run_widget.multithreaded else 1)

    def disable_all(self):
        self.centralWidget().setEnabled(False)

    def enable_all(self):
        self.centralWidget().setEnabled(True)