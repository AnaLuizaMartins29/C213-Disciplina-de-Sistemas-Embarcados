import numpy as np
import matplotlib.pyplot as plt
import scipy.io
import control as ctrl

#carregando dados do dataset
data = scipy.io.loadmat('Dataset_Grupo4_c213.mat')

t = data['tiempo'].flatten()
u = data['entrada'].flatten()
y = data['salida'].flatten()


#plot original do dataset 
plt.figure()

plt.subplot(2,1,1)
plt.plot(t, u)
plt.title('Entrada (u)')

plt.subplot(2,1,2)
plt.plot(t, y)
plt.title('Saída (y)')

plt.tight_layout()
plt.show()

# Calculando o ganho K
k = (y[-1] - y[0]) / (u[-1] - u[0])
print("k =", k)

# Encontrando o Atraso (θ)
dy = np.diff(y)
indice_theta = np.where(dy > 0.01)[0][0]
theta = t[indice_theta]
print("theta =", theta)


# Encontratando Tau (τ)
y_final = y[-1]
y_inicial = y[0]
y_63 = y_inicial + 0.63 * (y_final - y_inicial)

indice_tau = np.where(y >= y_63)[0][0]
t_tau = t[indice_tau]
tau = t_tau - theta
print("tau =", tau)

#valores encontrados 
#k = 0.9477
#θ = 7
#τ = 23


# sistema sem atraso
G = ctrl.TransferFunction([k], [tau, 1])

# aproximação de Padé (ordem 1 já serve)
num_delay, den_delay = ctrl.pade(theta, 1)

delay = ctrl.TransferFunction(num_delay, den_delay)

# sistema com atraso aproximado
G_delay = G * delay

print(G_delay)

# Simulação
t_out, y_out = ctrl.step_response(G_delay)

plt.figure()
plt.plot(t_out, y_out)
plt.title("Resposta do Modelo Identado")
plt.grid()

# Mostrar tudo
plt.show()


# Ziegler-Nichols

Kp = (1.2 * tau) / (k * theta)
Ti = 2 * theta
Td = 0.5 * theta

print("Ziegler-Nichols:")
print("Kp =", Kp)
print("Ti =", Ti)
print("Td =", Td)

# Controlador PID (forma paralela)
C = ctrl.TransferFunction(
    [Kp*Td, Kp, Kp/Ti],  # numerador
    [1, 0]               # denominador
)

T = ctrl.feedback(C * G_delay, 1)

t_pid, y_pid = ctrl.step_response(T)

plt.figure()
plt.plot(t_pid, y_pid)
plt.title("Resposta com PID - Ziegler-Nichols")
plt.grid()

info = ctrl.step_info(T)

print("\nMétricas da resposta:")
print(info)

#Cohen-Coon

R = theta / tau

Kp_cc = (1/k) * ( (4/3 + R/4) * (tau/theta) )
Ti_cc = theta * (32 + 6*R) / (13 + 8*R)
Td_cc = theta * (4 / (11 + 2*R))

print("\nCohen-Coon:")
print("Kp =", Kp_cc)
print("Ti =", Ti_cc)
print("Td =", Td_cc)

# PID Cohen-Coon
C_cc = ctrl.TransferFunction(
    [Kp_cc * Td_cc, Kp_cc, Kp_cc / Ti_cc],
    [1, 0]
)

# Malha fechada
T_cc = ctrl.feedback(C_cc * G_delay, 1)

# Resposta
t_cc, y_cc = ctrl.step_response(T_cc)

plt.figure()
plt.plot(t_cc, y_cc)
plt.title("Resposta com PID - Cohen-Coon")
plt.grid()

# Métricas
info_cc = ctrl.step_info(T_cc)

print("\nMétricas Cohen-Coon:")
print(info_cc)

plt.figure()
plt.plot(t_pid, y_pid, label="Ziegler-Nichols")
plt.plot(t_cc, y_cc, label="Cohen-Coon")
plt.legend()
plt.title("Comparação dos Métodos PID")
plt.grid()
plt.show()

plt.savefig("comparacao_PID.png")