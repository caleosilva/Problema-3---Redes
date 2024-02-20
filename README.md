<div align="center">
  <h1>
      Relatório do problema 3: ZapsZap Release Candidate
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

Nos últimos anos, a crescente relevância dos aplicativos de mensagens no contexto empresarial tem se destacado como uma ferramenta fundamental para otimizar a comunicação entre indivíduos e equipes. No entanto, depender de serviços de terceiros nem sempre é a alternativa mais adequada, especialmente quando requisitos essenciais de arquitetura e confiabilidade não são totalmente atendidos.

Diante desse cenário, uma startup decidiu investir no desenvolvimento de uma nova solução de mensagens instantâneas voltada para o mercado corporativo. Essa inovação é fundamentada no modelo peer-to-peer (P2P), com o objetivo de oferecer uma abordagem descentralizada, eliminando a necessidade de um servidor central. Além disso, há um foco na confiabilidade, alcançada por meio da implementação do modelo de difusão confiável baseado em ACK, assegurando que todos os usuários sempre possuam as mesmas mensagens.

A materialização desse sistema foi realizada por meio da linguagem de programação Python, na versão 3.11, e suas bibliotecas internas, que incluem threading, socket, time e queue. A escolha de desenvolver e testar o produto utilizando containers Docker reflete o comprometimento com a eficiência e a consistência. Para garantir uma comunicação eficaz, a implementação foi construída sobre uma arquitetura de rede baseada em UDP. Esse conjunto de decisões tecnológicas e ferramentas resultou na criação de um sistema robusto e eficiente, capaz de atender plenamente às demandas específicas da startup.

# 2. Metodologia

### 2.1 - Ordenação

A eficiente ordenação em sistemas distribuídos representa um componente crucial para assegurar a consistência e a integridade das operações realizadas em ambientes onde diversas entidades interagem de forma descentralizada. Dentre as várias abordagens disponíveis, a utilização do Relógio Lógico de Lamport destaca-se como uma solução sólida e viável para enfrentar os desafios inerentes a esse cenário.

O Relógio Lógico de Lamport, proposto por Leslie Lamport na década de 1970, fundamenta-se na lógica temporal, permitindo a ordenação parcial de eventos em um ambiente distribuído. Sua relevância em sistemas distribuídos reside na capacidade de proporcionar uma noção coesa de tempo, mesmo quando os diversos nodos não compartilham uma fonte de tempo global.

Ao optar pelo Relógio Lógico de Lamport, destacam-se benefícios significativos. Primeiramente, sua implementação é reconhecida pela simplicidade e eficiência. O processo, baseado na atribuição de carimbos de tempo a eventos, facilita a integração em ambientes distribuídos, contribuindo para a efetiva realização de transações e operações.

A independência do Relógio Lógico de Lamport de uma infraestrutura global de tempo é um fator determinante. Essa característica é particularmente útil em ambientes nos quais a sincronização temporal global pode ser impraticável, permitindo uma adaptação flexível a ambientes dinâmicos e variáveis.

Por meio dessa estratégia, a ordenação das mensagens no sistema desenvolvido baseia-se em dois atributos fundamentais: o carimbo de data/hora do relógio lógico e um identificador exclusivo de cada usuário. Essa abordagem assegura, de maneira eficaz, que a sequência das mensagens seja uniforme e consistente em todos os nós do sistema.

### 2.2 - Pacotes

Para que os objetivos fossem alcançados, 3 diferentes classes de pacotes foram desenvolvidos e por meio deles a comunicação entre diferentes usuários é feita. Essas classes são as seguintes:

1. **Heartbeat**:

&nbsp;&nbsp;&nbsp;&nbsp;A classe de pacotes denominada heartbeat possui como propósito verificar quem está online ou não através de pulsos em um intervalo de tempo (semelhante a batida de coração). Aqui há dois tipos de pacotes, sendo eles um de solicitação e outro de resposta. 

&nbsp;&nbsp;&nbsp;&nbsp;Conforme o exemplo abaixo, a cada 0.4 segundos é enviado o pacote multicast de solicitação para todos os usuário do grupo. Cada um que receber, deve de imediato devolver o pacote unicast de resposta para quem o solicitou afim de informar que o mesmo está online.

   * __Pacote de solicitação__ = _```{'type': 'hb', 'src': {} }```_
   * __Pacote de resposta__ = _```{'type': 'hbr', 'src': {} }```_

&nbsp;&nbsp;&nbsp;&nbsp;Através dessa troca de pacotes, é definido o status de cada usuário, que varia entre "on" para online, "unk" para desconhecido e "off" para offline. Caso o usuário pare de responder as solicitações de heartbeat, ele fica como "unk" durante 4 segundos. Caso ultrapasse esse tempo e ainda assim não responda, ele é dado como offline.

2. **Mensagem**:

&nbsp;&nbsp;&nbsp;&nbsp;No que diz respeito aos pacotes de mensagens, aqui encontramos 3 pacotes que são complementares e através deles o modelo de difusão confiável baseado em ACK é implementado, sendo eles: 
   * __Pacote de envio__ = _```{'type': 'msg', 'time': '', 'msg': '', 'sender': {} }```_
   * __Pacote de confimação de recebimento__ = _```{'type': 'ack', 'time': '', 'sender': {} }```_
   * __Pacote informando que todos receberam e pode exibir__  = _```{'type': 'show', 'time': '', 'sender': {} }```_

&nbsp;&nbsp;&nbsp;&nbsp;Com base nos pacotes mencionados acima, quando um usuário envia uma mensagem, ele a transmite em multicast para todos os usuários online. Todos os destinatários que recebem a mensagem, por sua vez, realizam uma transmissão unicast de volta para o remetente com um pacote de confirmação de recebimento.

&nbsp;&nbsp;&nbsp;&nbsp;Posteriormente, se o remetente perceber que todos os destinatários confirmaram o recebimento, ele envia um pacote de autorização para exibição da mensagem para esses destinatários. Vale ressaltar que esse último pacote, além de ser transmitido em multicast para todos os usuários online, utiliza o conceito de um algoritmo de difusão probabilística. Isso significa que cada usuário envia o pacote para todos os outros, reduzindo assim a probabilidade de perda por parte de qualquer destinatário.

5. **Sincronização**: Quanto a sincronização, ela é feita sempre que o usuário saí e entra no programa, afim de cumprir o requisito de que todos os nós tenham exatamente as mesmas mensagens. Para que isso fosse possível, foram desenvolvidos 6 pacotes distintos para que ocorresse da forma esperada.
   * __Solicitação de sincronização__ = _```{'type': 'sync_list_req', 'src': {} }```_
   * __Verificação da necessidade__ = _```{'type': 'sync_list_verify', 'src': {} }```_
   * __Resposta quanto a necessidade__ = _```{'type': 'sync_list_req_index', 'src': {} }```_
   * __Envio dos id's de todas as mensagens__ = _```{'type': 'sync_list_resp_index', 'id_operation': '', 'src': {}, pkg_number: '', 'pkg_total': '', 'index': []}```_
   * __Com os id's recebidos, solicita o envio das mensagens__ = _```{'type': 'sync_list_req_msg', 'src': {} }```_
   * __Pacote com 1/n mensagem de sincronização, sendo n o total__ = _```{'type': 'sync_list_resp_msg', 'src': {}, 'msg': {} }```_

&nbsp;&nbsp;&nbsp;&nbsp;Quando o sistema é iniciado, ele envia uma solicitação de sincronização para todos os nós que não estão offline. O primeiro nó a responder torna-se o par temporário e é encarregado de enviar tanto a lista contendo os IDs de todas as mensagens quanto as mensagens em si para o novo nó. Esse procedimento foi implementado para garantir o controle em caso de perda de mensagens, pois o receptor terá conhecimento das mensagens que recebeu, uma vez que o envio de cada mensagem é realizado individualmente.


### 2.3 - Threads

O software desenvolvido opera com base em nove Threads distintas, cada uma desempenhando um papel específico ao longo de toda a execução do sistema. Estas Threads são as seguintes:

1. **serverSYNC**: Tem a função primordial de receber todos os pacotes de sincronização que chegam, adicionando-os a uma fila para processamento posterior.
2. **serverHB**: Responsável por receber todos os pacotes de heartbeat, colocando-os a uma fila para que seja processado em um momento futuro.
3. **serverMSG**: Encarregado de receber todos os pacotes de mensagem, acrescentando-os em uma fila para serem processados na sequência.
4. **handle_request**: Operando sequencialmente às Threads anteriores, a `handle_request` verifica a fila de pacotes e os trata de acordo com seus propósitos, garantindo uma abordagem sequencial no processamento.
5. **heartbeat**: Esta thread tem como objetivo enviar os pacotes de solicitação heartbeat para todos os nós que pertecem ao grupo.
6. **update_status**: Responsável por determinar os status de membro do grupo, o colocando com "on", "unk" ou "off" com base na resposta das solicitações do heartbeat.
7. **check_ack_remove_waiting_list**: Tem como objetivo verificar se as mensagens enviadas por seu nó foram recebidas por todos usuários para que a mesma seja exibida.
8. **send_message**: Thread desenvolvida para realizar o envio de mensagens para o usuário e salvar a sua lista de mensagens em um arquivo de texto.
9. **show_all_pkg_received**: Por fim, de maneira opicional, está thread atua como um quadro informativo, apresentando de forma imediata todos os pacotes recebidos para que hajá uma noção visual por parte do usuário em cada nó.

# 3. Resultados

Ao iniciar o sistema, o usuário é recebido por um menu de login simples e intuitivo, proporcionando uma entrada descomplicada no ambiente de comunicação. Após concluir o login, é automaticamente direcionado ao grupo específico ao qual está vinculado. É importante destacar que, embora o sistema possa suportar várias conversas, atualmente, apenas um grupo está cadastrado, sendo este acessado automaticamente após o login. Ao entrar no grupo, todas as sincronizações necessárias são realizadas, garantindo a recepção das mensagens trocadas durante períodos offline.

Para testar o sistema, a thread **send_message** também foi programada para enviar 100 mensagens sequenciais caso seja digitado "bot". Isso permite testar o sistema com um alto fluxo de troca de pacotes em todos os nós. Além disso, caso seja escrito "save", essa thread salvará todas as mensagens em um arquivo de texto.

Cada nó do grupo mantém duas listas principais que armazenam as mensagens em dois estados distintos. A primeira é a lista de espera, onde a mensagem permanece até que todos os destinatários a recebam e o pacote autorizando a exibição seja enviado. Após o recebimento desse pacote, a mensagem é movida para a lista de confirmação (ack), que contém exclusivamente as mensagens que todos os nós do grupo possuem.

Enfatizamos o compromisso com a robustez e segurança no desenvolvimento do sistema. O tratamento adequado de todos os possíveis erros e exceções garante a estabilidade das operações, contribuindo para uma experiência positiva dos usuários. Qualquer intercorrência, como falhas na comunicação, é identificada e tratada de maneira eficaz, proporcionando feedback claro e útil aos usuários. Em resumo, o sistema não apenas oferece uma interface amigável para comunicação, mas também reforça a segurança e privacidade de todos os envolvidos.

# 4. Conclusão

Durante a conclusão deste projeto, adquirimos insights valiosos sobre a intrincada interconexão de sistemas distribuídos, destacando a complexidade inerente à sincronização desses sistemas. Exploramos detalhadamente a dinâmica da comunicação UDP, juntamente com o algoritmo de difusão probabilística e difusão confiável baseado em ACK, ampliando nossos conhecimentos em diversas áreas da arquitetura de sistemas distribuídos.

É gratificante observar que todos os requisitos estabelecidos foram plenamente atendidos, evidenciando a eficácia do sistema implementado. A correta ordenação das mensagens no ambiente distribuído foi assegurada, assim como a sincronização adequada das mensagens, mesmo aquelas enviadas durante os períodos offline do usuário. Também foi constatado que todos os nós do grupo sempre possuem as mesmas mensagens.

Ao vislumbrar o futuro do projeto, identificamos uma área passível de aprimoramento e desenvolvimento: a inclusão de novos grupos e a implementação de um sistema de criptografia. Aprimorar esses aspectos seria uma estratégia válida, visando fortalecer ainda mais a privacidade dos usuários do sistema e ampliar a comunicação. Essa possível evolução contribuiria para consolidar o projeto como uma solução robusta e confiável no cenário de sistemas distribuídos.

# Referências

Python threading module: Disponível em: https://docs.python.org/3/library/threading.html. Acesso em: 23 de ago. de 2023

HUNT, John; HUNT, John. Sockets in Python. Advanced Guide to Python 3 Programming, p. 457-470, 2019.

