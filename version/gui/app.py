import sys
from PyQt5.QtCore import (Qt, QSize, pyqtSignal, QThread, QEvent, QTimer)
from PyQt5.QtGui import (QPixmap, QIcon, QMouseEvent)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel, QStackedLayout, QToolBar, QMenuBar,
							 QSizePolicy, QMenu, QAction, QLineEdit,
							 QSplitter, QMessageBox, QFileDialog)
from . import series
from . import gui_constants, misc
from ..database import fetch

class AppWindow(QMainWindow):
	"The application's main window"
	def __init__(self):
		super().__init__()
		self.center = QWidget()
		self.display = QStackedLayout()
		self.center.setLayout(self.display)
		# init the manga view variables
		self.manga_display()
		# init the chapter view variables
		self.chapter_display()
		# init toolbar
		self.init_toolbar()
		# init status bar
		self.init_stat_bar()

		self.display.addWidget(self.manga_main)
		self.display.addWidget(self.chapter_main)

		self.setCentralWidget(self.center)
		self.setWindowTitle("Happypanda")
		self.resize(1029, 650)
		self.show()
	
	def init_stat_bar(self):
		self.status_bar = self.statusBar()
		self.status_bar.setMaximumHeight(20)
		self.status_bar.setSizeGripEnabled(False)
		self.stat_info = QLabel()
		self.stat_info.setIndent(5)
		self.sort_main = QAction("Asc", self)
		sort_menu = QMenu()
		self.sort_main.setMenu(sort_menu)
		s_by_title = QAction("Title", sort_menu)
		s_by_artist = QAction("Artist", sort_menu)
		sort_menu.addAction(s_by_title)
		sort_menu.addAction(s_by_artist)
		self.status_bar.addPermanentWidget(self.stat_info)
		#self.status_bar.addAction(self.sort_main)
		self.temp_msg = QLabel()
		self.temp_timer = QTimer()
		self.manga_list_view.series_model.ROWCOUNT_CHANGE.connect(self.stat_row_info)
		self.manga_list_view.series_model.STATUSBAR_MSG.connect(self.stat_temp_msg)

	def stat_temp_msg(self, msg):
		self.temp_timer.stop()
		self.temp_msg.setText(msg)
		self.status_bar.addWidget(self.temp_msg)
		self.temp_timer.timeout.connect(self.temp_msg.clear)
		self.temp_timer.setSingleShot(True)
		self.temp_timer.start(5000)

	def stat_row_info(self):
		r = self.manga_list_view.series_model.rowCount()
		t = len(self.manga_list_view.series_model._data)
		self.stat_info.setText("<b>Showing {} of {} </b>".format(r, t))

	def manga_display(self):
		"initiates the manga view"
		self.manga_main = QWidget()
		self.manga_main.setContentsMargins(-10, -12, -10, -10)
		self.manga_view = QHBoxLayout()
		self.manga_main.setLayout(self.manga_view)

		manga_delegate = series.CustomDelegate()
		manga_delegate.BUTTON_CLICKED.connect(self.setCurrentIndex)
		self.manga_list_view = series.MangaView()
		self.manga_list_view.setItemDelegate(manga_delegate)
		self.manga_view.addWidget(self.manga_list_view)

	def favourite_display(self):
		"initiates favourite display"
		pass

	def chapter_display(self):
		"Initiates chapter view"
		self.chapter_main = QWidget()
		self.chapter_main.setObjectName("chapter_main") # to allow styling this object
		self.chapter_layout = QHBoxLayout()
		self.chapter_main.setLayout(self.chapter_layout)

		#self.chapter_info.setContentsMargins(-8,-7,-7,-7)
		#self.chapter_info.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
		self.chapter_info_view = series.ChapterInfo()
		self.chapter_layout.addWidget(self.chapter_info_view)

		chapter_list_view = series.ChapterView()
		self.chapter_layout.addWidget(chapter_list_view)
		#self.chapter.setCollapsible(0, True)
		#self.chapter.setCollapsible(1, False)

	def init_toolbar(self):
		self.toolbar = QToolBar()
		self.toolbar.setFixedHeight(30)
		self.toolbar.setWindowTitle("Show") # text for the contextmenu
		#self.toolbar.setStyleSheet("QToolBar {border:0px}") # make it user defined?
		self.toolbar.setMovable(False)
		self.toolbar.setFloatable(False)
		#self.toolbar.setIconSize(QSize(20,20))
		self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

		spacer_start = QWidget() # aligns the first actions properly
		spacer_start.setFixedSize(QSize(10, 1))
		self.toolbar.addWidget(spacer_start)

		favourite_view_icon = QIcon(gui_constants.STAR_BTN_PATH)
		favourite_view_action = QAction(favourite_view_icon, "Favourite", self)
		#favourite_view_action.setText("Manga View")
		favourite_view_action.triggered.connect(lambda: self.setCurrentIndex(1)) #need lambda to pass extra args
		self.toolbar.addAction(favourite_view_action)

		catalog_view_icon = QIcon(gui_constants.HOME_BTN_PATH)
		catalog_view_action = QAction(catalog_view_icon, "Library", self)
		#catalog_view_action.setText("Catalog")
		catalog_view_action.triggered.connect(lambda: self.setCurrentIndex(0)) #need lambda to pass extra args
		self.toolbar.addAction(catalog_view_action)
		self.toolbar.addSeparator()

		series_icon = QIcon(gui_constants.PLUS_PATH)
		series_action = QAction(series_icon, "Add series...", self)
		series_action.triggered.connect(self.manga_list_view.SERIES_DIALOG.emit)
		series_menu = QMenu()
		series_menu.addSeparator()
		populate_action = QAction("Populate from folder...", self)
		populate_action.triggered.connect(self.populate)
		series_menu.addAction(populate_action)
		series_action.setMenu(series_menu)
		self.toolbar.addAction(series_action)

		spacer_middle = QWidget() # aligns buttons to the right
		spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.toolbar.addWidget(spacer_middle)
		
		self.search_bar = QLineEdit()
		self.search_bar.setPlaceholderText("Search title, artist, genres")
		self.search_bar.setMaximumWidth(200)
		self.toolbar.addWidget(self.search_bar)
		self.toolbar.addSeparator()
		settings_icon = QIcon(gui_constants.SETTINGS_PATH)
		settings_action = QAction(settings_icon, "Set&tings", self)
		self.toolbar.addAction(settings_action)
		self.addToolBar(self.toolbar)
		
		spacer_end = QWidget() # aligns About action properly
		spacer_end.setFixedSize(QSize(10, 1))
		self.toolbar.addWidget(spacer_end)

	def setCurrentIndex(self, number, index=None):
		"""Changes the current display view.
		Params:
			number <- int (0 for manga view, 1 for chapter view
		Optional:
			index <- QModelIndex for chapter view
		Note: 0-based indexing
		"""
		if index is not None:
			self.chapter_info_view.display_manga(index)
			self.display.setCurrentIndex(number)
		else:
			self.display.setCurrentIndex(number)

	# TODO: Improve this so that it adds to the series dialog,
	# so user can edit data before inserting (make it a choice)
	def populate(self):
		"Populates the database with series from local drive'"
		msgbox = QMessageBox()
		msgbox.setText("<font color='red'><b>Use with care.</b></font> Choose a folder containing all your series'.")
		msgbox.setInformativeText("Oniichan, are you sure you want to do this?")
		msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		msgbox.setDefaultButton(QMessageBox.No)
		if msgbox.exec() == QMessageBox.Yes:
			path = QFileDialog.getExistingDirectory(None, "Choose a folder containing your series'")
			if len(path) is not 0:
				data_thread = QThread()
				loading_thread = QThread()
				loading = misc.Loading()

				if not loading.ON:
					misc.Loading.ON = True
					fetch_instance = fetch.Fetch()
					fetch_instance.series_path = path
					loading.show()

					def finished(status):
						if status:
							self.manga_list_view.series_model.populate_data()
							# TODO: make it spawn a dialog instead (from utils.py or misc.py)
							if loading.progress.maximum() == loading.progress.value():
								misc.Loading.ON = False
								loading.hide()
							data_thread.quit
						else:
							loading.setText("<font color=red>An error occured. Try restarting..</font>")
							loading.progress.setStyleSheet("background-color:red")
							data_thread.quit

					def fetch_deleteLater():
						try:
							fetch_instance.deleteLater
						except NameError:
							pass

					def thread_deleteLater(): #NOTE: Isn't this bad?
						data_thread.deleteLater

					def a_progress(prog):
						loading.progress.setValue(prog)
						loading.setText("Searching on local disk...\n(Will take a while on first time)")

					fetch_instance.moveToThread(data_thread)
					fetch_instance.DATA_COUNT.connect(loading.progress.setMaximum)
					fetch_instance.PROGRESS.connect(a_progress)
					data_thread.started.connect(fetch_instance.local)
					fetch_instance.FINISHED.connect(finished)
					fetch_instance.FINISHED.connect(fetch_deleteLater)
					fetch_instance.FINISHED.connect(thread_deleteLater)
					data_thread.start()


if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")