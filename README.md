<div align="center">
  <h1>
      Relatório do problema 2: ZapsZap
  </h1>

  <h3>
    Georgenes Caleo Silva Pinheiro
  </h3>

  <p>
    Engenharia de Computação – Universidade Estadual de Feira de Santana (UEFS)
    Av. Transnordestina, s/n, Novo Horizonte
    Feira de Santana – BA, Brasil – 44036-900
  </p>

  <center>caleosilva75@gmail.com</center>

</div>

# 1. Introdução

Nos últimos anos, a crescente importância dos aplicativos de mensagens no ambiente corporativo tem se destacado como uma ferramenta fundamental para aprimorar a comunicação entre indivíduos e equipes. No entanto, depender de serviços de terceiros nem sempre é a opção mais ideal, especialmente quando requisitos cruciais de arquitetura e segurança não são plenamente atendidos.

Nesse cenário, uma startup optou por investir no desenvolvimento de uma nova solução de mensagens instantâneas direcionada ao mercado corporativo. Essa inovação baseia-se no modelo peer-to-peer (P2P), visando oferecer uma abordagem descentralizada, eliminando a necessidade de um servidor central. Além disso, a ênfase está na segurança da comunicação, com a implementação de mensagens criptografadas.

A concretização desse sistema ocorreu por meio da linguagem de programação Python, versão 3.11, e suas bibliotecas internas, incluindo threading, socket, time e queue. A decisão de desenvolver e testar o produto utilizando containers Docker reflete o comprometimento com a eficiência e a consistência. Para garantir uma comunicação eficaz, a implementação foi construída sobre a arquitetura de rede baseada em UDP. Esse conjunto de escolhas tecnológicas e ferramentas resultou na criação de um sistema robusto e eficiente, capaz de atender plenamente às demandas específicas da startup.

# 2. Metodologia

### 2.1 - Sincronização

A sincronização eficiente em sistemas distribuídos é um componente crucial para garantir a consistência e a integridade das operações realizadas em ambientes onde diferentes entidades interagem de maneira descentralizada. Dentre as diversas abordagens disponíveis, a utilização do Relógio Lógico de Lamport destaca-se como uma solução viável e robusta para endereçar os desafios inerentes a esse contexto.

O Relógio Lógico de Lamport, proposto por Leslie Lamport na década de 1970, fundamenta-se na lógica temporal, permitindo a ordenação parcial de eventos em um ambiente distribuído. A sua viabilidade em sistemas distribuídos reside na capacidade de fornecer uma noção coerente de tempo, mesmo quando os diferentes nodos não possuem uma fonte de tempo global compartilhada.

Ao optar pelo Relógio Lógico de Lamport, destacam-se benefícios significativos. Primeiramente, sua implementação é reconhecida por sua simplicidade e eficiência. O processo baseado na atribuição de carimbos de tempo a eventos facilita a integração em ambientes distribuídos, contribuindo para uma coordenação efetiva de transações e operações.

A independência do Relógio Lógico de Lamport de uma infraestrutura global de tempo é um fator determinante. Essa característica é particularmente valiosa em ambientes nos quais a sincronização temporal global pode ser impraticável, permitindo a adaptação flexível a ambientes dinâmicos e variáveis.

Por meio dessa estratégia, a ordenação das mensagens é conduzida por meio de dois atributos fundamentais: o timestamp do relógio lógico e um identificador único gerado pela biblioteca uuid. Essa abordagem garante de maneira eficaz que a sequência das mensagens seja uniforme e consistente em todos os nós do sistema.

### 2.2 - Pacotes

Para que os objetivos fossem alcançados, 5 diferentes pacotes foram estabelecidos e por meio deles a comunicação entre diferentes usuários é feita. Estes pacotes são os seguintes:

1. **Pacote de mensagem**: { type: msg, time: ‘ ’,  id: ‘ ’, msg: ‘ ’, sender: { } }
   * type: string que identifica o tipo de pacote.
   * time: Timestamp do relógio lógico de quem enviou a mensagem.
   * id: String única que identifica a mensagem.
   * msg: A própria mensagem que foi enviada.
   * sender: Endereço de quem a enviou.

2. **Solicitação do timestamp dos usuários**: { type: sync_clock, time: ‘ ’, sender: { } }
   * type: string que identifica o tipo de pacote.
   * time: Timestamp do relógio lógico de quem enviou a mensagem.
   * sender: Endereço de quem a enviou.

3. **Resposta da solicitação do timestamp**: { type: sync_clock_response, time: ‘ ’, sender: { } }
   * type: string que identifica o tipo de pacote.
   * time: Timestamp do relógio lógico de quem enviou a mensagem.
   * sender: Endereço de quem a enviou.

4. **Solicitação da lista de mensagens dos usuários**:  { type: sync_list_request, sender: { } }
   * type: string que identifica o tipo de pacote.
   * sender: Endereço de quem a enviou.

5. **Resposta da solicitação da lista de mensagens**: { type: sync_list_response, id_list: ‘ ’, size: ‘ ‘, body: { } }
   * type: string que identifica o tipo de pacote.
   * id_list: Número aleatório que identifica a lista a ser enviada.
   * size: Quantidade total de mensagens da lista a ser enviada.
   * body: Informações da mensagem (time, id, msg e sender).

### 2.3 - Threads

O software desenvolvido opera com base em seis Threads distintas, cada uma desempenhando um papel específico ao longo de toda a execução do sistema. Estas Threads são as seguintes:

1. **server_thread**: Iniciada como a primeira Thread do sistema, tem a função primordial de receber todos os pacotes que chegam, adicionando-os a uma fila para processamento posterior.
2. **handle_request_thread**: Operando sequencialmente à Thread anterior, a `handle_request_thread` acompanha a fila de pacotes e os trata de acordo com seus propósitos, garantindo uma abordagem sequencial no processamento.
3. **sync_clock_and_list_thread**: Esta Thread visa contatar todos os usuários ativos, realizando solicitações de sincronização de relógio lógico e mensagens. Seu propósito é manter uma coesão temporal e garantir a integridade das mensagens.
4. **receive_dict_sync_thread**: Responsável por receber as mensagens relacionadas à sincronização do sistema, esta Thread adiciona à lista de mensagens aquelas que estão ausentes e as organiza de maneira ordenada.
5. **write_prepare_message_thread**: Como sugere o nome, esta Thread se encarrega de capturar as mensagens escritas pelo usuário e prepará-las para serem enviadas aos demais, garantindo a eficiência na comunicação.
6. **sync_active_thread**: Por fim, a última Thread iniciada é responsável por realizar a sincronização a cada 10 segundos das mensagens entre todos os usuários ativos, contribuindo para uma experiência contínua e atualizada.

### 2.4 - Criptografia

A estratégia de criptografia adotada neste sistema é baseada em um método simples conhecido como deslocamento fixo, onde cada caractere na mensagem original é substituído por outro caractere que se encontra a uma distância fixa no alfabeto. Essa distância é representada por uma constante denominada SHIFT_AMOUNT que pode ser alterada para cada grupo ou conversa.

Essencialmente, durante a criptografia, cada caractere na mensagem é deslocado à frente no alfabeto por um número fixo de posições, determinado pela constante SHIFT_AMOUNT. Por exemplo, se SHIFT_AMOUNT for 3, a letra 'A' seria substituída por 'D', 'B' por 'E', e assim por diante. Da mesma forma, durante a descriptografia, a operação é revertida, movendo cada caractere de volta no alfabeto.

Ao escolher essa abordagem, priorizamos a simplicidade de implementação. O código é claro e fácil de entender, o que facilita a manutenção e o entendimento mesmo para aqueles que não têm experiência extensiva em criptografia. Além disso, essa estratégia oferece uma solução leve e eficiente.

No entanto, essa simplicidade vem com algumas desvantagens significativas. A vulnerabilidade a ataques de força bruta é um ponto a ser destacado, já que um atacante pode explorar a previsibilidade do método para decifrar mensagens. Além disso, a ausência de uma chave dinâmica torna o sistema menos adaptável a ameaças persistentes.


# 3. Resultados

Ao iniciar o sistema, o usuário é recepcionado por um menu de login simples e intuitivo, estabelecendo uma entrada facilitada ao ambiente de comunicação. Após concluir o login, é imediatamente direcionado ao grupo específico ao qual está vinculado. Importante ressaltar que, embora o sistema possa oferecer múltiplas conversas, atualmente, apenas um grupo está cadastrado, sendo este automaticamente acessado após o login.

Ao adentrar o grupo, todas as sincronizações necessárias são efetuadas, garantindo a recepção das mensagens trocadas durante períodos offline. Em um ambiente distribuído, mesmo quando online, a cada 10 segundos cada usuário compartilha sua lista de mensagens, assegurando que todos possuam a versão completa da conversa.

Destacamos o compromisso com a robustez e segurança no desenvolvimento do sistema. Tratamento adequado de todos os possíveis erros e exceções assegura a estabilidade das operações, contribuindo para a experiência positiva dos funcionários. Qualquer intercorrência, como falhas na comunicação, é identificada e tratada de maneira eficaz, proporcionando feedback claro e útil aos usuários. Em síntese, o sistema não apenas oferece uma interface amigável para comunicação, mas também reforça a segurança e privacidade de todos os envolvidos.

# 4. Conclusão

Durante a conclusão deste projeto, alcançamos insights valiosos sobre a complexa interconexão de sistemas distribuídos, destacando-se a complexidade inerente à sincronização desses sistemas. Exploramos de forma aprofundada a dinâmica da comunicação UDP, enriquecendo nossos conhecimentos em diversas áreas da arquitetura de sistemas distribuídos.

É gratificante observar que todos os requisitos estabelecidos foram plenamente atendidos, demonstrando a eficiência do sistema implementado. A correta ordenação das mensagens no ambiente distribuído foi assegurada, assim como a sincronização adequada das mensagens, mesmo aquelas enviadas durante períodos offline do usuário. Ademais, as mensagens possuem uma camada de criptografia, assegurando a privacidade do usuário.

Olhando para o futuro do projeto, identificamos uma área passível de aprimoramento: o sistema de criptografia. Aprimorar esse aspecto seria uma opção válida, visando fortalecer ainda mais a privacidade dos usuários do sistema, garantindo uma camada adicional de segurança às suas comunicações. Essa evolução potencial contribuiria para consolidar o projeto como uma solução robusta e confiável no cenário de sistemas distribuídos.

# Referências

Python threading module: Disponível em: https://docs.python.org/3/library/threading.html. Acesso em: 23 de ago. de 2023

HUNT, John; HUNT, John. Sockets in Python. Advanced Guide to Python 3 Programming, p. 457-470, 2019.

