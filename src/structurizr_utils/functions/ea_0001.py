from structurizr_utils.functions.objects import FitnessStatus, Assessment, AssessmentObjects
from structurizr_utils.models.models_product import get_product_infra

from typing import List, Dict, Any, Set, Union
import logging
import ipaddress

# Настройка логгера для модуля
logger = logging.getLogger(__name__)



def is_external_ip(ip: Union[str, ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
    """
    Проверяет, является ли IP-адрес внешним (не принадлежит приватным/локальным подсетям).
    
    Args:
        ip: IP-адрес в виде строки или объекта ipaddress
        
    Returns:
        True если IP внешний, False если приватный/локальный
    """
    # Приватные IPv4 сети (RFC 1918)
    private_ipv4_networks = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
    ]
    
    # Специальные IPv4 сети
    special_ipv4_networks = [
        ipaddress.ip_network('0.0.0.0/8'),           # Текущая сеть
        ipaddress.ip_network('100.64.0.0/10'),       # CGNAT (RFC 6598)
        ipaddress.ip_network('127.0.0.0/8'),         # Loopback
        ipaddress.ip_network('169.254.0.0/16'),      # Link-local
        ipaddress.ip_network('192.0.0.0/24'),        # IETF Protocol Assignments
        ipaddress.ip_network('192.0.2.0/24'),        # TEST-NET-1
        ipaddress.ip_network('192.88.99.0/24'),      # 6to4 Relay
        ipaddress.ip_network('198.18.0.0/15'),       # Network benchmark tests
        ipaddress.ip_network('198.51.100.0/24'),     # TEST-NET-2
        ipaddress.ip_network('203.0.113.0/24'),      # TEST-NET-3
        ipaddress.ip_network('224.0.0.0/4'),         # Multicast
        ipaddress.ip_network('240.0.0.0/4'),         # Reserved
        ipaddress.ip_network('255.255.255.255/32'),  # Limited broadcast
    ]
    
    # Приватные IPv6 сети
    private_ipv6_networks = [
        ipaddress.ip_network('::1/128'),             # Loopback
        ipaddress.ip_network('::/128'),              # Unspecified
        ipaddress.ip_network('fc00::/7'),            # Unique local (ULA)
        ipaddress.ip_network('fe80::/10'),           # Link-local
        ipaddress.ip_network('ff00::/8'),            # Multicast
        ipaddress.ip_network('2001:db8::/32'),       # Documentation
        ipaddress.ip_network('::ffff:0:0/96'),       # IPv4-mapped
        ipaddress.ip_network('64:ff9b::/96'),        # IPv4/IPv6 translation
        ipaddress.ip_network('2002::/16'),           # 6to4
    ]
    
    try:
        if isinstance(ip, str):
            ip_obj = ipaddress.ip_address(ip)
        else:
            ip_obj = ip
            
        if ip_obj.version == 4:
            all_private = private_ipv4_networks + special_ipv4_networks
        else:
            all_private = private_ipv6_networks
            
        return not any(ip_obj in network for network in all_private)
        
    except ValueError:
        return False

def check_string_for_external_ip(text: str) -> tuple[bool, list[str]]:
    """
    Проверяет строку на наличие external IP-адресов.
    
    Args:
        text: Строка для проверки
        
    Returns:
        (True если есть хотя бы один внешний IP, список всех внешних IP)
    """
    import re
    
    # Паттерны для поиска IP-адресов
    ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|' \
                   r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:|' \
                   r'\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b|' \
                   r'\b(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}\b|' \
                   r'\b(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}\b|' \
                   r'\b(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}\b|' \
                   r'\b(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}\b|' \
                   r'\b[0-9a-fA-F]{1,4}:(?::[0-9a-fA-F]{1,4}){1,6}\b|' \
                   r'\b:(?::[0-9a-fA-F]{1,4}){1,7}\b|' \
                   r'\b::\b'
    
    external_ips = []
    
    # Поиск IPv4
    for match in re.finditer(ipv4_pattern, text):
        ip = match.group()
        if is_external_ip(ip):
            external_ips.append(ip)
            
    # Поиск IPv6
    for match in re.finditer(ipv6_pattern, text):
        ip = match.group()
        if is_external_ip(ip):
            external_ips.append(ip)
    
    return bool(external_ips), external_ips

def check_ea_0001(cmdb: str, data: Dict[str, Any], backend_url: str, 
                    share_url: str, publish: bool, product_id : int = -1) -> List[FitnessStatus]:

    logger.info(f'Начинаем проверку EA.0001 для системы CMDB: {cmdb}')
    
    result: List[FitnessStatus] = []
        
    result.append(check_external_services(cmdb=cmdb,data=data,backend_url=backend_url,share_url=share_url))

    logger.info(f'Проверка EA.0001 завершена для системы {cmdb}. Результатов: {len(result)}')

    return result


def check_external_services(cmdb : str, data: Dict[str, Any], backend_url: str, share_url: str) -> FitnessStatus:
    environments: Set[str] = set()
    queue = list()

    found_external_nodes: List[Dict[str, str]] = []

    for deployment_node in data.get('model', {}).get('deploymentNodes', []):
        environment: str = deployment_node.get('environment', '')
        if environment:
            for child in deployment_node.get('children',[]):
                queue.append(child)                        
            logger.info(f'Найден deployment environment: {environment}')


    while len(queue) > 0:
        deployment_node = queue.pop(0)
        deployment_node_type = deployment_node.get('properties',{}).get('type',None)
        is_has_instances = len(deployment_node.get('containerInstances',[]))>0
        name = deployment_node.get('name','')

        ip = deployment_node.get('properties',{}).get('ip',None)
        host = deployment_node.get('properties',{}).get('host',None)
        external_ip = deployment_node.get('properties',{}).get('external_ip',None)

        already_external = False
        if ip:
            has_external,ips = check_string_for_external_ip(ip)
            if has_external:
                found_external_nodes.append({name:f"{ips}"})
                already_external = True

        if external_ip and not already_external:
            found_external_nodes.append({name:f"'{external_ip}'"})

        if host and not already_external:
            if host.lower().endswith(".beeline.ru"):
                found_external_nodes.append({name:f"{host}"})


        for child in deployment_node.get('children',[]):
                queue.append(child)


    if len(found_external_nodes)>0:
        assessment_obj_found: AssessmentObjects = {
            "isCheck": True,
            "details": found_external_nodes
        }
        return FitnessStatus(
            code="EA.0001",
            isCheck=True,
            resultDetails='Приложение имеет выход в интернет',
            assessmentDescription='Приложение имеет выход в интернет',
            assessmentObjects=[assessment_obj_found]
        )

    return FitnessStatus(
        code="EA.0001",
        isCheck=False,
        resultDetails='Приложение не имеет выход в интернет',
        assessmentDescription='Приложение не имеет выход в интернет',
        assessmentObjects=[]
    )