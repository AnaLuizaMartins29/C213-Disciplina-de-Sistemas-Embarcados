# C213-Disciplina-de-Sistemas-Embarcados

Controle de Temperatura de Forno Equipe:

Ana Luiza Martins
Jéssica Guerzoni
Objetivo:

- Controlar o ajuste de temperatura de um forno de modo que haja menos oscilações possíveis em relação a temperatura ideal
Métodos utilizados para comparação:

- Método Ziegler-Nichols
- Método Cohen-Coon
  
Controlador PID O controlador PID é responsável por ajustar a resposta do sistema. • Kp (Proporcional): responde ao erro atual • Ti (Integral): elimina erro acumulado • Td (Derivativo): antecipa o comportamento

Modos de Operação

- Automático: parâmetros calculados automaticamente (ZN ou CC)
- Manual: usuário define Kp, Ti e Td livremente
Setpoint:

- O sistema utiliza um setpoint normalizado (valor 1), representando a temperatura desejada do forno.
- 
Métricas de Desempenho:

- Overshoot: quanto o sistema ultrapassa o valor desejado
- Tempo de resposta: rapidez para atingir o setpoint
- Estabilidade: ausência de oscilações
- 
Funcionamento do Sistema:

- O usuário seleciona o modo de operação e define os parâmetros. O backend simula a resposta do sistema e o frontend exibe o gráfico da temperatura ao longo do tempo.
- 
Conclusão:

- O projeto demonstra na prática o funcionamento de controladores PID e permite comparar diferentes métodos de sintonia, evidenciando suas vantagens e desvantagens.
