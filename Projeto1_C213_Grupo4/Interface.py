import sys
import numpy as np
import scipy.io
import control as ctrl
import mplcursors

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QFileDialog, QComboBox, QLineEdit
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class Interface(QWidget):
    def __init__(self):
        super().__init__()

        # DADOS
        self.t = None
        self.u = None
        self.y = None

        # PARÂMETROS DO SISTEMA
        self.k = None
        self.tau = None
        self.theta = None
        self.ess_open = None

        self.T_max = 100

        # CONFIGURAÇÕES DA JANELA
        self.setWindowTitle("Controle de Forno - PID C213")
        self.setGeometry(100, 100, 1100, 650)

        layout = QVBoxLayout()

        # ABAS
        self.tabs = QTabWidget()
        self.tab_id = QWidget()
        self.tab_pid = QWidget()
        self.tab_comp = QWidget()

        self.tabs.addTab(self.tab_id, "Identificação")
        self.tabs.addTab(self.tab_pid, "Controle PID")
        self.tabs.addTab(self.tab_comp, "Comparação")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # Inicialização das abas
        self.init_identificacao()
        self.init_pid()
        self.init_comparacao()

    # IDENTIFICAÇÃO
    def init_identificacao(self):
        main_layout = QVBoxLayout()

        # Título
        titulo = QLabel("Controle de temperatura para forno")
        titulo.setStyleSheet("font-size:18px; font-weight:bold;")

        # Botões superiores
        top = QHBoxLayout()
        self.btn_load = QPushButton("Carregar Dataset")
        self.btn_id = QPushButton("Identificar Sistema")

        self.btn_load.clicked.connect(self.load_data)
        self.btn_id.clicked.connect(self.identify)

        top.addWidget(self.btn_load)
        top.addWidget(self.btn_id)

        # Área principal
        content = QHBoxLayout()

        # Gráfico do dataset
        self.fig_data = Figure()
        self.canvas_data = FigureCanvas(self.fig_data)
        content.addWidget(self.canvas_data, 3)

        # Painel lateral com parâmetros
        painel = QVBoxLayout()
        painel.addWidget(QLabel("Identificação do Sistema"))

        self.k_label = QLabel("k: -")
        self.tau_label = QLabel("τ: -")
        self.theta_label = QLabel("θ: -")
        self.ess_label = QLabel("ESS: -")

        for w in [self.k_label, self.tau_label, self.theta_label, self.ess_label]:
            w.setStyleSheet("font-size:14px; padding:6px; border:1px solid gray;")
            painel.addWidget(w)

        painel.addStretch()
        content.addLayout(painel, 1)

        self.label_status = QLabel("Status: aguardando dataset")

        # Montagem final
        main_layout.addWidget(titulo)
        main_layout.addLayout(top)
        main_layout.addWidget(self.label_status)
        main_layout.addLayout(content)

        self.tab_id.setLayout(main_layout)

    def load_data(self):
        file, _ = QFileDialog.getOpenFileName(self, "Selecionar dataset", "", "*.mat")

        if file:
            data = scipy.io.loadmat(file)

            # Carrega dados
            self.t = data['tiempo'].flatten()
            self.u = data['entrada'].flatten()
            self.y = data['salida'].flatten()

            self.label_status.setText("Status: Dataset carregado")

            # Plot dos dados
            self.fig_data.clear()

            ax1 = self.fig_data.add_subplot(211)
            ax2 = self.fig_data.add_subplot(212)

            ax1.plot(self.t, self.u, color='blue')
            ax2.plot(self.t, self.y, color='red')

            ax1.set_title("Entrada (Potência %)")
            ax1.set_ylabel("%")
            ax1.grid()

            ax2.set_title("Saída (Temperatura °C)")
            ax2.set_xlabel("Tempo (s)")
            ax2.set_ylabel("°C")
            ax2.grid()

            self.fig_data.tight_layout()
            self.canvas_data.draw()

    def identify(self):
        if self.y is None:
            return

        # Cálculo dos parâmetros
        self.k = (self.y[-1] - self.y[0]) / (self.u[-1] - self.u[0])

        dy = np.diff(self.y)
        self.theta = self.t[np.where(dy > 0.01)[0][0]]

        y63 = self.y[0] + 0.63 * (self.y[-1] - self.y[0])
        self.tau = self.t[np.where(self.y >= y63)[0][0]] - self.theta

        # Erro em regime permanente (malha aberta)
        self.ess_open = abs(self.y[-1] - self.y[0])

        # Atualiza interface
        self.k_label.setText(f"k: {self.k:.3f}")
        self.tau_label.setText(f"τ: {self.tau:.2f}s")
        self.theta_label.setText(f"θ: {self.theta:.2f}s")
        self.ess_label.setText(f"ESS: {self.ess_open:.2f}°C")

    # PID
    def init_pid(self):
        layout = QHBoxLayout()

        left = QVBoxLayout()
        right = QVBoxLayout()

        # Gráfico PID
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        left.addWidget(self.canvas)

        # Controles
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

        # Botão exportar gráfico
        self.btn_export = QPushButton("Exportar Gráfico")
        self.btn_export.clicked.connect(self.export_graph)

        self.label_result = QLabel("Painel de Métricas")

        # Layout lateral
        for w in [
            QLabel("Método"), self.combo_method,
            QLabel("Modo"), self.combo_mode,
            QLabel("Kp"), self.kp,
            QLabel("Ti"), self.ti,
            QLabel("Td"), self.td,
            QLabel("Setpoint (°C)"), self.sp,
            btn,
            self.btn_export,
            self.label_result
        ]:
            right.addWidget(w)

        layout.addLayout(left, 2)
        layout.addLayout(right, 1)

        self.tab_pid.setLayout(layout)
        self.toggle_manual()

    def export_graph(self):
        file, _ = QFileDialog.getSaveFileName(self, "Salvar gráfico", "", "PNG (*.png)")
        if file:
            self.figure.savefig(file)

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
        sp = float(self.sp.text())

        # Sintonia PID
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

        # Planta
        G = ctrl.TransferFunction([self.k], [self.tau, 1])
        num, den = ctrl.pade(self.theta, 1)
        plant = G * ctrl.TransferFunction(num, den)

        # Controlador
        C = ctrl.TransferFunction([Kp*Td, Kp, Kp/Ti], [1, 0])
        T = ctrl.feedback(C * plant, 1)

        t, y = ctrl.step_response(T)
        temp = y * sp

        info = ctrl.step_info(T)

        # Plot
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        ax.plot(t, temp, label="Temperatura")
        ax.axhline(sp, linestyle="--", label="Setpoint")

        # Marcadores importantes
        peak = np.max(temp)
        t_peak = t[np.argmax(temp)]
        ax.plot(t_peak, peak, 'ro')
        ax.annotate("Pico", (t_peak, peak), xytext=(0, 10),
                    textcoords="offset points", ha='center')

        if info['RiseTime']:
            tr = info['RiseTime']
            idx_tr = np.where(t >= tr)[0][0]
            y_tr = temp[idx_tr]
            ax.plot(tr, y_tr, 'go')
            ax.annotate("Tr", (tr, y_tr), xytext=(0, 10),
                        textcoords="offset points", ha='center')

        if info['SettlingTime']:
            ts = info['SettlingTime']
            idx_ts = np.where(t >= ts)[0][0]
            y_ts = temp[idx_ts]
            ax.plot(ts, y_ts, 'mo')
            ax.annotate("Ts", (ts, y_ts), xytext=(0, 10),
                        textcoords="offset points", ha='center')

        # Cursor interativo
        cursor = mplcursors.cursor(ax.lines, hover=True)

        @cursor.connect("add")
        def on_add(sel):
            x, y = sel.target
            sel.annotation.set_text(f"{x:.2f}s\n{y:.2f}°C")

        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Temperatura (°C)")
        ax.legend()
        ax.grid()

        self.canvas.draw()

        # Métricas
        self.label_result.setText(
            f"tr: {info['RiseTime']:.2f}s\n"
            f"ts: {info['SettlingTime']:.2f}s\n"
            f"Mp: {info['Overshoot']:.2f}%"
        )

    # COMPARAÇÃO
    def init_comparacao(self):
        layout = QVBoxLayout()

        self.btn = QPushButton("Comparar")
        self.btn.clicked.connect(self.compare)

        self.fig2 = Figure()
        self.canvas2 = FigureCanvas(self.fig2)

        layout.addWidget(self.btn)
        layout.addWidget(self.canvas2)

        self.tab_comp.setLayout(layout)

    def compare(self):
        if self.k is None:
            return

        sp = float(self.sp.text())

        R = self.theta / self.tau

        # Parâmetros ZN
        Kp1 = (1.2 * self.tau) / (self.k * self.theta)
        Ti1 = 2 * self.theta
        Td1 = 0.5 * self.theta

        # Parâmetros CC
        Kp2 = (1/self.k) * ((4/3 + R/4) * (self.tau/self.theta))
        Ti2 = self.theta * (32 + 6*R) / (13 + 8*R)
        Td2 = self.theta * (4 / (11 + 2*R))

        G = ctrl.TransferFunction([self.k], [self.tau, 1])
        num, den = ctrl.pade(self.theta, 1)
        plant = G * ctrl.TransferFunction(num, den)

        # Malha aberta
        t_open, y_open = ctrl.step_response(plant)

        def sim(Kp, Ti, Td):
            C = ctrl.TransferFunction([Kp*Td, Kp, Kp/Ti], [1, 0])
            T = ctrl.feedback(C * plant, 1)
            return ctrl.step_response(T)

        t1, y1 = sim(Kp1, Ti1, Td1)
        t2, y2 = sim(Kp2, Ti2, Td2)

        self.fig2.clear()
        ax = self.fig2.add_subplot(111)

        ax.plot(t_open, y_open * sp, '--', label="Malha Aberta")
        ax.plot(t1, y1 * sp, label="ZN")
        ax.plot(t2, y2 * sp, label="CC")
        ax.axhline(sp, linestyle="--", label="Setpoint")

        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Temperatura (°C)")
        ax.legend()
        ax.grid()

        self.canvas2.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Interface()
    w.show()
    sys.exit(app.exec_())