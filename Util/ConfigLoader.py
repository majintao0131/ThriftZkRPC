# -* - coding: UTF-8 -* -
__author__ = 'jintao'

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

MAX_CONFIG_DEEP = 10

class ConfigLoader:
    def __init__(self, path):
        self.__path = path
        self.__configs = {}
        self.__level = 0

    def init(self):
        return self._load_config()

    def _load_config(self):
        root = ET.parse(self.__path).getroot()
        if not root:
            return False

        children = root.getchildren()

        (result, zk_node) = self._load_children(root)
        if not result:
            return False

        self.__configs[root.tag] = zk_node
        return True

    def _load_children(self, node):
        if self.__level >= MAX_CONFIG_DEEP:
            return (False, None)
        self.__level += 1

        children = node.getchildren()
        if len(children) == 0:
            self.__level -= 1
            return (True, node.text)
        else:
            node_dict = {}
            for child in node:
                node_name = child.tag
                (result, zk_node) = self._load_children(child)
                if not result:
                    return False
                if node_name not in node_dict:
                    node_dict[node_name] = zk_node
                else:
                    if type(node_dict[node_name]) == list:
                        node_dict[node_name].append(zk_node)
                    else:
                        value_list = [node_dict[node_name]]
                        value_list.append(zk_node)
                        node_dict[node_name] = value_list

            self.__level -= 1
            return (True, node_dict)

    def value(self, *args):
        node = self.__configs
        for value in args:
            node = node[value]
            if not node:
                return None
        return node



