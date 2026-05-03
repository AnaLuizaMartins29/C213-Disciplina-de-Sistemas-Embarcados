import sys
import numpy as np
import scipy.io
import control as ctrl

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QFileDialog, QComboBox, QLineEdit, QTextEdit
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class Interface(QWidget):
    def __init__(self):
        super().__init__()

        # Dados
        self.t = None
        self.u = None
        self.y = None

        # Sistema
        self.k = None
        self.tau = None
        self.theta = None

        # Escala forno
        self.T_max = 100

        self.setWindowTitle("Controle de Forno - PID C213")
        self.setGeometry(100, 100, 1100, 650)

        layout = QVBoxLayout()

        self.tabs = QTabWidget()

        self.tab_id = QWidget()
        self.tab_pid = QWidget()
        self.tab_comp = QWidget()

        self.tabs.addTab(self.tab_id, "Identificação")
        self.tabs.addTab(self.tab_pid, "Controle PID")
        self.tabs.addTab(self.tab_comp, "Comparação")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.init_identificacao()
        self.init_pid()
        self.init_comparacao()

    # ================= IDENTIFICAÇÃO =================
    def init_identificacao(self):
        layout = QVBoxLayout()

        # ===== TOPO (BOTÕES) =====
        top = QHBoxLayout()

        self.btn_load = QPushButton("Carregar Dataset")
        self.btn_id = QPushButton("Identificar Sistema")

        self.btn_load.clicked.connect(self.load_data)
        self.btn_id.clicked.connect(self.identify)

        top.addWidget(self.btn_load)
        top.addWidget(self.btn_id)

        # ===== STATUS =====
        self.label_status = QLabel("Status: aguardando dataset")

        # ===== DADOS =====
        self.data_view = QTextEdit()
        self.data_view.setReadOnly(True)

        # ===== RESULTADO =====
        self.result_view = QLabel("Resultado da identificação aparecerá aqui")

        layout.addLayout(top)
        layout.addWidget(self.label_status)
        layout.addWidget(QLabel("Dados do Dataset:"))
        layout.addWidget(self.data_view)
        layout.addWidget(QLabel("Identificação:"))
        layout.addWidget(self.result_view)

        self.tab_id.setLayout(layout)

    def load_data(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar dataset", "", "*.mat")

        if file:
            data = scipy.io.loadmat(file)

            self.t = data['tiempo'].flatten()
            self.u = data['entrada'].flatten()
            self.y = data['salida'].flatten()

            self.label_status.setText("Status: Dataset carregado")

            # mostrar dados (resumo)
            preview = "t: " + str(self.t[:10]) + "\n\n"
            preview += "u: " + str(self.u[:10]) + "\n\n"
            preview += "y: " + str(self.y[:10])

            self.data_view.setText(preview)

    def identify(self):
        if self.y is None:
            self.result_view.setText("Carregue o dataset primeiro!")
            return

        self.k = (self.y[-1] - self.y[0]) / (self.u[-1] - self.u[0])

        dy = np.diff(self.y)
        self.theta = self.t[np.where(dy > 0.01)[0][0]]

        y63 = self.y[0] + 0.63 * (self.y[-1] - self.y[0])
        self.tau = self.t[np.where(self.y >= y63)[0][0]] - self.theta

        self.result_view.setText(
            f"k = {self.k:.3f} | θ = {self.theta:.2f} | τ = {self.tau:.2f}"
        )

    # ================= PID =================
    def init_pid(self):
        layout = QHBoxLayout()

        left = QVBoxLayout()
        right = QVBoxLayout()

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        left.addWidget(self.canvas)

        self.combo_method = QComboBox()
        self.combo_method.addItems(["Ziegler-Nichols", "Cohen-Coon"])

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Automático", "Manual"])
        self.combo_mode.currentIndexChanged.connect(self.toggle_manual)

        self.kp = QLineEdit()
        self.ti = QLineEdit()
        self.td = QLineEdit()

        self.sp = QLineEdit("100")

        btn = QPushButton("Simular")
        btn.clicked.connect(self.simulate)

        self.label_result = QLabel("Resultados")

        right.addWidget(QLabel("Método"))
        right.addWidget(self.combo_method)

        right.addWidget(QLabel("Modo"))
        right.addWidget(self.combo_mode)

        right.addWidget(QLabel("Kp"))
        right.addWidget(self.kp)

        right.addWidget(QLabel("Ti"))
        right.addWidget(self.ti)

        right.addWidget(QLabel("Td"))
        right.addWidget(self.td)

        right.addWidget(QLabel("Setpoint (°C)"))
        right.addWidget(self.sp)

        right.addWidget(btn)
        right.addWidget(self.label_result)

        layout.addLayout(left, 2)
        layout.addLayout(right, 1)

        self.tab_pid.setLayout(layout)

        self.toggle_manual()

    def toggle_manual(self):
        manual = self.combo_mode.currentText() == "Manual"
        self.kp.setEnabled(manual)
        self.ti.setEnabled(manual)
        self.td.setEnabled(manual)

    def simulate(self):
        if self.k is None:
            return

        method = self.combo_method.currentText()
        mode = self.combo_mode.currentText()

        if mode == "Automático":
            if method == "Ziegler-Nichols":
                Kp = (1.2 * self.tau) / (self.k * self.theta)
                Ti = 2 * self.theta
                Td = 0.5 * self.theta
            else:
                R = self.theta / self.tau
                Kp = (1/self.k) * ((4/3 + R/4) * (self.tau/self.theta))
                Ti = self.theta * (32 + 6*R) / (13 + 8*R)
                Td = self.theta * (4 / (11 + 2*R))
        else:
            Kp = float(self.kp.text())
            Ti = float(self.ti.text())
            Td = float(self.td.text())

        G = ctrl.TransferFunction([self.k], [self.tau, 1])
        num, den = ctrl.pade(self.theta, 1)
        plant = G * ctrl.TransferFunction(num, den)

        C = ctrl.TransferFunction([Kp*Td, Kp, Kp/Ti], [1, 0])
        T = ctrl.feedback(C * plant, 1)

        t, y = ctrl.step_response(T)

        temp = y * self.T_max
        sp = float(self.sp.text())

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        ax.plot(t, temp, label="Temperatura (°C)")
        ax.axhline(sp, linestyle="--", label="Setpoint")

        ax.set_title("Forno Industrial")
        ax.set_xlabel("Tempo")
        ax.set_ylabel("Temperatura (°C)")
        ax.grid()
        ax.legend()

        self.canvas.draw()

        info = ctrl.step_info(T)

        self.label_result.setText(
            f"Kp={Kp:.2f} Ti={Ti:.2f} Td={Td:.2f}\n"
            f"Tr={info['RiseTime']:.2f}s Ts={info['SettlingTime']:.2f}s Mp={info['Overshoot']:.2f}%"
        )

    # ================= COMPARAÇÃO =================
    def init_comparacao(self):
        layout = QVBoxLayout()

        self.btn = QPushButton("Comparar ZN vs CC")
        self.btn.clicked.connect(self.compare)

        self.fig2 = Figure()
        self.canvas2 = FigureCanvas(self.fig2)

        layout.addWidget(self.btn)
        layout.addWidget(self.canvas2)

        self.tab_comp.setLayout(layout)

    def compare(self):
        if self.k is None:
            return

        R = self.theta / self.tau

        Kp1 = (1.2 * self.tau) / (self.k * self.theta)
        Ti1 = 2 * self.theta
        Td1 = 0.5 * self.theta

        Kp2 = (1/self.k) * ((4/3 + R/4) * (self.tau/self.theta))
        Ti2 = self.theta * (32 + 6*R) / (13 + 8*R)
        Td2 = self.theta * (4 / (11 + 2*R))

        def sim(Kp, Ti, Td):
            G = ctrl.TransferFunction([self.k], [self.tau, 1])
            num, den = ctrl.pade(self.theta, 1)
            plant = G * ctrl.TransferFunction(num, den)
            C = ctrl.TransferFunction([Kp*Td, Kp, Kp/Ti], [1, 0])
            T = ctrl.feedback(C * plant, 1)
            return ctrl.step_response(T)

        t1, y1 = sim(Kp1, Ti1, Td1)
        t2, y2 = sim(Kp2, Ti2, Td2)

        self.fig2.clear()
        ax = self.fig2.add_subplot(111)

        ax.plot(t1, y1 * self.T_max, label="ZN")
        ax.plot(t2, y2 * self.T_max, label="CC")

        ax.set_title("Comparação Forno")
        ax.set_ylabel("Temperatura (°C)")
        ax.set_xlabel("Tempo")
        ax.legend()
        ax.grid()

        self.canvas2.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Interface()
    w.show()
    sys.exit(app.exec_())