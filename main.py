import sys
from PyQt5.QtWidgets import QApplication
import Servers
import System


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    app = QApplication(sys.argv)

    s = Servers.Servers_Socket()

    sys.exit(app.exec_())
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
