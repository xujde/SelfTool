import sys
from PyQt5.QtWidgets import QApplication

import ServersUI

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    app = QApplication(sys.argv)

    App = ServersUI.Servers_MainUI()

    sys.exit(app.exec_())
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
