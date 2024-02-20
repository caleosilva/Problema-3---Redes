import os
import json
import socket
import random
import time
import threading


lock = threading.Lock()

def clear_screen():
    if os.name == 'posix':
        os.system('clear')
    elif os.name == 'nt':
        os.system('cls')

# ================================================= NEW FEATURES =================================================

def send_message_to_address(objMsg, address, portName):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(json.dumps(objMsg).encode(), (address['host'], address[portName]))
    except Exception as e:
        print(e)
    finally:
        client_socket.close()

def send_message_to_all(objMsg, my_info, data_users, portName):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for user in data_users:
            if (my_info['id'] != user['id']):
                client_socket.sendto(json.dumps(objMsg).encode(), (user['host'], user[portName]))
    except Exception as e:
        print("Erro: ", e)
    finally:
        client_socket.close()

def send_message_to_on_unk(objMsg, my_info, users_status, portName):
    try:
        portNumberName = 1
        if (portName == 'portHB'):
            portNumberName = 4
        elif (portName == 'portMSG'):
            portNumberName = 5

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sended_to = []
        for key, value in users_status.items():
            if (key[3] != my_info['id']  and value['status'] in ['on', 'unk']):
                client_socket.sendto(json.dumps(objMsg).encode(), (key[0], key[portNumberName]))
                sended_to.append(key[3])                
        return sended_to
    except Exception as e:
        print(e)
    finally:
        client_socket.close()

def send_index_to_address(ack_msg_list, address, my_info, portName):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    id_operation = ''.join(str(random.randint(1, 100)) for _ in range(6))
    
    if (len(ack_msg_list) == 0):
        pacote = {
            'type': 'sync_list_resp_index',
            'id_operation': id_operation,
            'src': my_info,
            'pkg_number': '0',  # Número do pacote atual
            'pkg_total': '0',  # Número total de pacotes
            'index': []
        }
        pacote_json = json.dumps(pacote)
        client_socket.sendto(pacote_json.encode(), (address['host'], address[portName]))

    else:
        with lock:
            lista_index = [msg['time'] for msg in ack_msg_list]
        
        max_list_size = 125
        sub_listas = [lista_index[i:i+max_list_size] for i in range(0, len(lista_index), max_list_size)]

        # Para cada sub-lista, crie e envie um pacote
        for i, sub_lista in enumerate(sub_listas, start=1):
            pacote = {
                'type': 'sync_list_resp_index',
                'id_operation': id_operation,
                'src': my_info,
                'pkg_number': str(i),  # Número do pacote atual
                'pkg_total': str(len(sub_listas)),  # Número total de pacotes
                'index': sub_lista
            }
            
            pacote_json = json.dumps(pacote)
            client_socket.sendto(pacote_json.encode(), (address['host'], address[portName]))
            time.sleep(0.1)

    
    client_socket.close()

def send_all_msg_ack_to_address(ack_msg_list, address, my_info, portName):
    global lock
    batch_size = 10
    
    for i in range(0, len(ack_msg_list), batch_size):
        with lock:
            batch = ack_msg_list[i:i+batch_size]
        
        # Processar o lote fora do bloco de lock
        for msg_ack in batch:
            sync_list_resp_msg_pkg = {'type': 'sync_list_resp_msg', 'src': my_info, 'msg': msg_ack}
            send_message_to_address(sync_list_resp_msg_pkg, address, portName)
            time.sleep(0.1)  # Adicione um pequeno atraso entre cada envio de mensagem
        
        # Permitir que outras threads acessem a lista enquanto o lote está sendo processado
        time.sleep(1)

def check_index_list(index_list_sync):
    total_packets = {}  # Dicionário para rastrear o número total de pacotes esperados para cada id_operation
    received_packets = {}  # Dicionário para rastrear o número total de pacotes recebidos para cada id_operation
    
    # Iterar sobre cada elemento em index_list_sync
    for item in index_list_sync:
        id_operation = item['id_operation']
        pkg_number = int(item['pkg_number'])
        pkg_total = int(item['pkg_total'])
        
        # Atualizar o total de pacotes esperados para o id_operation atual
        if id_operation not in total_packets:
            total_packets[id_operation] = pkg_total
        
        # Atualizar o número total de pacotes recebidos para o id_operation atual
        if id_operation not in received_packets:
            received_packets[id_operation] = 0
        received_packets[id_operation] += 1
    
    # Verificar se o número total de pacotes recebidos é igual ao número total de pacotes esperados para cada id_operation
    for id_operation, total in total_packets.items():
        if id_operation not in received_packets or received_packets[id_operation] != total:
            return False  # Se os pacotes não chegaram completamente para qualquer id_operation, retorne False
    
    print("Index recebidos com sucesso!")
    return combine_packets_index_list(index_list_sync)

def combine_packets_index_list(index_list_sync):
    combined_packets = []
    for item in index_list_sync:
        index = item['index']
        combined_packets.extend(index)
    return combined_packets
    
def check_msg_ack_list_with_index_list(index_list_sync, msg_list_sync):
    tempos_index_list = set(index_list_sync)
    tempos_msg_list = {msg['time'] for msg in msg_list_sync}
    return tempos_index_list == tempos_msg_list

def add_msg_waiting_list(objMsg, waiting_list, my_info, type_msg, sended_to):
    global lock
    
    copia = (objMsg.copy())
    with lock:
        if (type_msg == 'sender'):
            copia['type'] = 'msg_src'
            copia['created_at'] = time.time()
            copia['sended_to'] = sended_to
            copia['received_ack']= []
            if copia not in waiting_list:
                waiting_list.append(copia)
            
        elif (type_msg == 'receiver'):
            copia['type'] = 'msg_dst'
            copia['created_at'] = time.time()
            if copia not in waiting_list:
                waiting_list.append(copia)

def update_waiting_list(objMsg, waiting_list, my_info):
    global lock

    with lock:
        for msg in waiting_list:
            if (msg['type'] == 'msg_src' and msg['time'] == objMsg['time']):
                msg['received_ack'].append(objMsg['src']['id'])

def handle_pck_show(pkg_show, waiting_msg_list, ack_msg_list, my_info, users_status):
    global lock

    with lock:
        waiting_msg_list_copy = list(waiting_msg_list)

    msg_to_remove = []
    for msg in waiting_msg_list_copy:        
        # Verifica se a mensagem ainda está na waiting_msg_list e trata isso.
        if (msg['time'] == pkg_show['time'] and msg['src'] == pkg_show['src']):
            pkg_show = {'type': 'show', 'time': msg['time'], 'src': msg['src']}
            send_message_to_on_unk(pkg_show, my_info, users_status, 'portMSG')
            msg_to_remove.append(msg)
            
            pure_message = {'time': msg['time'], 'msg': msg['msg'], 'src': msg['src']}
            if pure_message not in ack_msg_list:
                with lock:
                    ack_msg_list.append(pure_message)
            
    with lock:
        for msg_rmv in msg_to_remove:
            waiting_msg_list.remove(msg_rmv)
    
def ask_sync_clock_ackList(clock, my_info, users_status):
    clear_screen()
    print("Sincronizando...")
    time.sleep(1)
    
    sync_clock_pkg = {'type': 'sync_clock', 'time': clock.value, 'src': my_info}
    sended_to = send_message_to_on_unk(sync_clock_pkg, my_info, users_status, 'portSYNC')
    
    if len(sended_to) > 0:
        sync_list_pkg = {'type': 'sync_list_req', 'src': my_info}
        send_message_to_on_unk(sync_list_pkg, my_info, users_status, 'portSYNC')

def sort_messages(messages):
    sorted_messages = sorted(messages, key=lambda x: (x['time'], x['src']['id']))
    return sorted_messages
