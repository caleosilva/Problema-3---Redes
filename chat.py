import module
import socket
import threading
import json
import time
from queue import Queue
import sys

sync_complete = False
sync_expired = False
sync_init = False
lock = threading.Lock()

class LamportClock:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

    def update(self, received_time):
        with self.lock:
            self.value = max(self.value, received_time) + 1
            return self.value


def TESTER_send_message(clock, waiting_msg_list, my_info, users_status, ack_msg_list):
    time.sleep(1)
    while True:
        mensagem = input("")
        if (mensagem == "bot"):
            total = 101
            for i in range(1, total):
                objMsg = {'type': 'msg', 'time': clock.value, 'msg': str(i), 'src': my_info}
                sended_to = module.send_message_to_on_unk(objMsg, my_info, users_status, 'portMSG')
                module.add_msg_waiting_list(objMsg, waiting_msg_list, my_info, "sender", sended_to)
                clock.increment()
                time.sleep(0.1)
            print("Envio finalizado")
            
        elif (mensagem == "save"):
            list_name = f'lista{my_info["id"]}.txt'
            print("\n**Lista salva no arquivo: ", list_name, "**")
            sorted_messages = module.sort_messages(ack_msg_list)

            with open(list_name, "w") as f:
                for item in sorted_messages:
                    f.write(str(item) + "\n")
        else:
            objMsg = {'type': 'msg', 'time': clock.value, 'msg': mensagem, 'src': my_info}
            sended_to = module.send_message_to_on_unk(objMsg, my_info, users_status, 'portMSG')
            module.add_msg_waiting_list(objMsg, waiting_msg_list, my_info, "sender", sended_to)
            clock.increment()
            time.sleep(0.1)

def update_status(users_status, my_info):
    timestamp = time.time()
    for user_info in users_status.values():
        user_info['last_    update'] = timestamp
        
    while True:        
        for user_info_key, user_info_value in users_status.items():
            if user_info_key[3] != (my_info['id']):
                
                diferenca_tempo = time.time() - user_info_value['last_update']
                
                if (user_info_value['status'] == 'unk' and diferenca_tempo >= 4):
                    user_info_value['status'] = 'off'
                    user_info_value['last_update'] = time.time()

                elif (user_info_value['status'] == 'on' and diferenca_tempo > 1):
                    user_info_value['status'] = 'unk'
                    user_info_value['last_update'] = time.time()
            else:
                user_info_value['status'] = 'on'
                user_info_value['last_update'] = time.time()
        time.sleep(0.2)

def check_ack_remove_waiting_list(waiting_msg_list, ack_msg_list, my_info, users_status, lost_msg_list):
    global lock

    while True:

        with lock:
            waiting_msg_list_copy = list(waiting_msg_list)
        
        
        msg_to_remove = []
        for msg in waiting_msg_list_copy:
            seconds_passed = time.time() - msg['created_at']
            if (seconds_passed > 10):
                msg_to_remove.append(msg)
                lost_msg_list.append(msg)
            
            # Verifica se todos responderam com ack a mensagem enviada e autoriza para que seja motrada.
            if (msg['type'] == 'msg_src' and set(msg['sended_to']) == set(msg['received_ack'])):
                pkg_show = {'type': 'show', 'time': msg['time'], 'src': msg['src']}
                module.send_message_to_on_unk(pkg_show, my_info, users_status, 'portMSG')
                msg_to_remove.append(msg)
                
                pure_message = {'time': msg['time'], 'msg': msg['msg'], 'src': msg['src']}
                if (pure_message not in ack_msg_list):
                    with lock:
                        ack_msg_list.append(pure_message)
        
        try:
            with lock:
                for msg_rmv in msg_to_remove:
                    if msg_rmv in waiting_msg_list:
                        waiting_msg_list.remove(msg_rmv)
                    
        except Exception as e:
            print(e)

        time.sleep(0.5)

def heartbeat(my_info, data_users):
    while True:
        objIndentificadorLista = {'type': 'hb', 'src': my_info}
        module.send_message_to_all(objIndentificadorLista, my_info, data_users, 'portHB')
        time.sleep(0.4)

def serverSYNC(package_queue, my_info):
    tamanho_buffer = 8192
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, tamanho_buffer)
        server_adress = (my_info['host'], my_info['portSYNC'])
        server_socket.bind(server_adress)

        while True:
            data, client_address = server_socket.recvfrom(1024)
            dataObj = json.loads(data)
            package_queue.put(dataObj)
    except Exception as e:
        print("Erro ao logar:", e)

def serverHB(package_queue, my_info):
    tamanho_buffer = 8192
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, tamanho_buffer)
        server_adress = (my_info['host'], my_info['portHB'])
        server_socket.bind(server_adress)

        while True:
            data, client_address = server_socket.recvfrom(1024)
            dataObj = json.loads(data)
            package_queue.put(dataObj)
    except Exception as e:
        print("Erro ao logar:", e)

def serverMSG(package_queue, my_info):
    tamanho_buffer = 8192
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, tamanho_buffer)
        server_adress = (my_info['host'], my_info['portMSG'])
        server_socket.bind(server_adress)

        while True:
            data, client_address = server_socket.recvfrom(1024)
            dataObj = json.loads(data)
            package_queue.put(dataObj)
    except Exception as e:
        print("Erro ao logar:", e)

def ask_sync_clock_ackList(clock, my_info, users_status, time_stamp_sync):
    global sync_complete
    global sync_init
    global sync_expired

    module.clear_screen()
    print("******************************")
    print("*  Sincronizando mensagens   *")
    print("******************************\n")
    time.sleep(1)
    
    time_stamp_sync = time.time()

    sync_clock_pkg = {'type': 'sync_clock', 'time': clock.value, 'src': my_info}
    sended_to = module.send_message_to_on_unk(sync_clock_pkg, my_info, users_status, 'portSYNC')
    
    # Se tem alguem "on" ou "unk"
    if len(sended_to) > 0:
        sync_list_pkg = {'type': 'sync_list_req', 'src': my_info}
        module.send_message_to_on_unk(sync_list_pkg, my_info, users_status, 'portSYNC')

        while sync_complete == False:
            time_stamp_atual = time.time()
            if ((time_stamp_atual - time_stamp_sync) > 120):
                sync_expired = True
                break
            time.sleep(0.4)
    else:
        sync_complete = True

def handle_request(package_queue, my_info, users_status, waiting_msg_list, clock, ack_msg_list, index_list_sync, msg_list_sync, package_queue_show):
    global sync_complete
    global sync_init
    global sync_expired
    global lock

    needList = True
    idSeted = False
    idList = ''

    while True:
        
        message = package_queue.get()
        package_queue_show.put(message)

        try:
            # Pacotes para verificar quem está on, unk ou off:
            if message['type'] == 'hb':
                objIndentificador = {'type': 'hbr', 'src': my_info}
                module.send_message_to_address(objIndentificador, message['src'], 'portHB')
            elif message['type'] == 'hbr':
                users_status[tuple(message['src'].values())]['status'] = 'on'
                users_status[tuple(message['src'].values())]['last_update'] = time.time()               
            
            # Pacotes de controle de mensagens:
            elif message['type'] == 'msg':
                clock.update(message["time"])
                module.add_msg_waiting_list(message, waiting_msg_list, my_info, "receiver", sended_to=[])
                msg_ack = {'type': 'ack', 'time': message['time'], 'src': my_info}
                module.send_message_to_address(msg_ack, message['src'], 'portMSG')
            elif message['type'] == 'ack':
                module.update_waiting_list(message, waiting_msg_list, my_info)
            elif message['type'] == 'show':
                module.handle_pck_show(message, waiting_msg_list, ack_msg_list, my_info, users_status)
            
            # Pacotes de sincronização:
            # Clock:
            elif message['type'] == 'sync_clock':
                pkg_sync_response = {'type': 'sync_clock_response', 'time': clock.value, 'src': my_info}
                module.send_message_to_address(pkg_sync_response, message['src'], 'portSYNC')
            elif message['type'] == 'sync_clock_response':
                clock.update(message['time'])
            
            # Mensagens enquanto offline:
            elif message['type'] == 'sync_list_req':
                sync_list_verify_pkg = {'type': 'sync_list_verify', 'src': my_info}
                module.send_message_to_address(sync_list_verify_pkg, message['src'], 'portSYNC') 
            elif message['type'] == 'sync_list_verify':
                if (needList):
                    needList = False
                    sync_list_req_index = {'type': 'sync_list_req_index', 'src': my_info}
                    module.send_message_to_address(sync_list_req_index, message['src'], 'portSYNC')
            elif message['type'] == 'sync_list_req_index':
                module.send_index_to_address(ack_msg_list, message['src'], my_info, 'portSYNC')
            
            elif message['type'] == 'sync_list_resp_index':
                if (message['pkg_total'] != '0'):
                    sync_init = True
                    # Verificação caso receba mais de uma lista por algum motivo
                    if not idSeted:
                        idSeted = True
                        idList = message['id_operation']
                        
                    if idList == message['id_operation']:
                        index_list_sync.append(message)
                        is_complete = module.check_index_list(index_list_sync)
                        if is_complete:
                            sync_list_req_msg_pkg = {'type': 'sync_list_req_msg', 'src': my_info}
                            module.send_message_to_address(sync_list_req_msg_pkg, message['src'], 'portSYNC')
                            index_list_sync = is_complete
                else:
                    sync_complete = True
            
            elif message['type'] == 'sync_list_req_msg':
                # module.send_all_msg_ack_to_address(ack_msg_list, message['src'], my_info, 'portSYNC')
                end_all_msg_ack_to_address_thread = threading.Thread(target=module.send_all_msg_ack_to_address, args=(ack_msg_list, message['src'], my_info, 'portSYNC'))
                end_all_msg_ack_to_address_thread.daemon = True
                end_all_msg_ack_to_address_thread.start()
            
            elif message['type'] == 'sync_list_resp_msg':
                msg_list_sync.append(message['msg'])
                msg_list_complete = module.check_msg_ack_list_with_index_list(index_list_sync, msg_list_sync)  

                with lock:
                    if msg_list_complete:                  
                        sync_complete = msg_list_complete
                        for msg in msg_list_sync:
                            if msg not in ack_msg_list:
                                ack_msg_list.append(msg)
                        msg_list_sync.clear()
                        
            
        except Exception as e:
            print("Erro ao lidar com o request:", e)

def show_all_pkg_received(package_queue_show, waiting_msg_list, ack_msg_list, lost_msg_list, msg_list_sync):
    contadores = {
        "hb": 0,
        "hbr": 0,

        "msg": 0,
        "ack": 0,
        "show": 0,

        "sync_clock": 0,
        "sync_clock_response": 0,

        "sync_list_req": 0,
        "sync_list_verify": 0,
        "sync_list_req_index": 0,
        "sync_list_resp_index": 0,
        "sync_list_req_msg": 0,
        "sync_list_resp_msg": 0
    }
    
    counter = 0
    while True:
        pkg = package_queue_show.get()
        
        if pkg['type'] in contadores:
            contadores[pkg['type']] += 1
        
        counter += 1
        if  (counter % 3) == 0:   
            module.clear_screen()

            print("********************************  Pacotes recebidos  ********************************\n")

            # Exibir os contadores como uma tabela organizada
            print("{:<20} {:<20} {:<20} {:<20}".format("Tipo de Pacote", "Contador", "Tipo de Pacote", "Contador"))
            print("-" * 80)
            count = 0
            for key, value in contadores.items():
                if count % 2 == 0:
                    print("{:<20} {:<20}".format(key, value), end="")
                else:
                    print("{:<20} {:<20}".format(key, value))
                count += 1
            print("\n\n")  # Adicionando algumas linhas em branco para melhor visualização

            print("=============================  Tamanho das listas  =============================\n")

            print("{:<20} {:<20}".format("Lista", "Quantidade"))
            print("-" * 80)

            print("{:<20} {:<20}".format("Lista SYNC", len(msg_list_sync)))
            print("{:<20} {:<20}".format("Lista de espera", len(waiting_msg_list)))
            print("{:<20} {:<20}".format("Lista msg perdidas", len(lost_msg_list)))
            print("{:<20} {:<20}".format("Lista ACK", len(ack_msg_list)))     

def main():
    data_users = [
    {"host": '172.16.103.1', "portSYNC": 1111, "nome": "Amancio", "id": '1', "portHB": 1110, "portMSG": 1119},
    {"host": '172.16.103.2', "portSYNC": 2222, "nome": "Augusto", "id": '2', "portHB": 2220, "portMSG": 2229},
    {"host": '172.16.103.3', "portSYNC": 3333, "nome": "Maria", "id": '3', "portHB": 3330, "portMSG": 3339},
    {"host": '172.16.103.4', "portSYNC": 4444, "nome": "Emily", "id": '4', "portHB": 4440, "portMSG": 4449},
    {"host": '172.16.103.5', "portSYNC": 5555, "nome": "João", "id": '5', "portHB": 5550, "portMSG": 5559},
    {"host": '172.16.103.6', "portSYNC": 6666, "nome": "Laura", "id": '6', "portHB": 6660, "portMSG": 6669},
    {"host": '172.16.103.7', "portSYNC": 7777, "nome": "Pedro", "id": '7', "portHB": 7770, "portMSG": 7779},
    {"host": '172.16.103.8', "portSYNC": 8888, "nome": "Sophia", "id": '8', "portHB": 8880, "portMSG": 8889},
    {"host": '172.16.103.9', "portSYNC": 9999, "nome": "Lucas", "id": '9', "portHB": 9990, "portMSG": 9999},
    {"host": '172.16.103.10', "portSYNC": 1010, "nome": "Isabela", "id": '10', "portHB": 10100, "portMSG": 10109},
    {"host": '172.16.103.11', "portSYNC": 1111, "nome": "Enzo", "id": '11', "portHB": 11110, "portMSG": 11119},
    {"host": '127.0.0.1', "portSYNC": 1212, "nome": "Julia", "id": '12', "portHB": 12120, "portMSG": 12129},
    {"host": '127.0.0.1', "portSYNC": 1313, "nome": "Gabriel", "id": '13', "portHB": 13130, "portMSG": 13139},
    {"host": '127.0.0.1', "portSYNC": 1414, "nome": "Sophie", "id": '14', "portHB": 14140, "portMSG": 14149},
    {"host": '127.0.0.1', "portSYNC": 1515, "nome": "Matheus", "id": '15', "portHB": 15150, "portMSG": 15159}
]

    my_info = {'host': '', 'portSYNC': '', 'nome': '', "id": '', "portHB": '', "portMSG": ''}
    
    print('-=-=-=-= BEM VINDO =-=-=-=-\n\n')
    print('[1] -> Login')
    print('[2] -> Sair\n')
    opc = input("-> ")
    if opc == '1':
        print("\nUsuários:")
        for i, user in enumerate(data_users):
            print(f"{i + 1}. {user['nome']} - ({user['host']})")
        try:
            escolha = int(input("\nDigite o número correspondente ao usuário desejado: "))
            if 1 <= escolha <= len(data_users):
                selected_user = data_users[escolha - 1]
                my_info['host'] = selected_user['host']

                my_info['portSYNC'] = selected_user['portSYNC']
                my_info['portHB'] = selected_user['portHB']
                my_info['portMSG'] = selected_user['portMSG']
                
                my_info['nome'] = selected_user['nome']
                my_info['id'] = selected_user['id']

                start(my_info, data_users)
            else:
                print("Escolha inválida. Tente novamente.")
        except ValueError:
            print("Entrada inválida. Digite um número.")
    elif opc == '2':
        exit()

def start(my_info, data_users):
    global sync_complete
    global sync_init
    global sync_expired
  
    users_status = {tuple(user_info.values()): {'status': 'off', 'last_update': 0} for user_info in data_users}
    
    clock = LamportClock()
    package_queue = Queue()
    package_queue_show = Queue()

    
    index_list_sync = []
    msg_list_sync = []
    time_stamp_sync = 0

    waiting_msg_list = []
    ack_msg_list = []
    lost_msg_list = []

    
    serverSYNC_thread = threading.Thread(target=serverSYNC, args=(package_queue, my_info))
    serverSYNC_thread.daemon = True
    serverSYNC_thread.start()

    serverHB_thread = threading.Thread(target=serverHB, args=(package_queue, my_info))
    serverHB_thread.daemon = True
    serverHB_thread.start()

    serverMSG_thread = threading.Thread(target=serverMSG, args=(package_queue, my_info))
    serverMSG_thread.daemon = True
    serverMSG_thread.start()
    
    handle_request_thread = threading.Thread(target=handle_request, args=(package_queue, my_info, users_status, waiting_msg_list, clock, ack_msg_list, index_list_sync, msg_list_sync, package_queue_show))
    handle_request_thread.daemon = True
    handle_request_thread.start()
    
    heartbeat_thread = threading.Thread(target=heartbeat, args=(my_info, data_users))
    heartbeat_thread.daemon = True
    heartbeat_thread.start()
    
    update_status_thread = threading.Thread(target=update_status, args=(users_status, my_info))
    update_status_thread.daemon = True
    update_status_thread.start()

    show_all_pkg_received_thread = threading.Thread(target=show_all_pkg_received, args=(package_queue_show, waiting_msg_list, ack_msg_list, lost_msg_list, msg_list_sync))
    show_all_pkg_received_thread.daemon = True
    show_all_pkg_received_thread.start()

    ask_sync_clock_ackList(clock, my_info, users_status, time_stamp_sync)

    if (sync_complete):
        print("**#Sincronização finalizada#**")
    elif (sync_init and sync_complete == False):
        print("\n\nSincronização não completada. Tente novamente!")
        return
    elif (sync_expired == True):
        print("\n\nSincronização expirada. Tente novamente!")
        return

    TESTER_send_message_thread = threading.Thread(target=TESTER_send_message, args=(clock, waiting_msg_list, my_info, users_status, ack_msg_list))
    TESTER_send_message_thread.daemon = True
    TESTER_send_message_thread.start()
    
    check_ack_remove_waiting_list_thread = threading.Thread(target=check_ack_remove_waiting_list, args=(waiting_msg_list, ack_msg_list, my_info, users_status, lost_msg_list))
    check_ack_remove_waiting_list_thread.daemon = True
    check_ack_remove_waiting_list_thread.start()
    
    while True:
        time.sleep(100)

if __name__ == "__main__":
    main()