from copy import copy, deepcopy
from collections import deque
from blockchain_utils import BlockchainUtils as BU
from . import six_subset as six

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


class DAGValidationError(Exception):
    pass


class DAGNode(object):
    def __init__(self, block, edges=None):
        self.block = block
        self.edges = []

class DAG(object):

    def __init__(self):
        """ Construct a new DAG with no nodes or edges. """
        self.graph = {}

    def add_node(self, block):
        """ Add a node if it does not exist yet, or error out. """
        if block.node_id in self.graph:
            raise KeyError('node %s already exists' % block.node_id)
        self.graph[block.node_id] = DAGNode(block)

    def add_node_chain(self, node_id, graph):
        self.graph[node_id] = graph[node_id]
        for blocks in self.predecessors(node_id, graph):
            self.add_node_chain(blocks, graph)

    def leaf_selection(self, block, gnode_id, X_CENTER, Y_CENTER):
        x1 = block.coords[1]
        y1 = block.coords[2]

        def compare_x(a):
            if x1 < X_CENTER:
                return a < X_CENTER
            else:
                return a > X_CENTER

        def compare_y(a):
            if y1 < Y_CENTER:
                return a < Y_CENTER
            else:
                return a > Y_CENTER

        for node_id in self.ind_nodes():
            x2 = self.graph[node_id].block.coords[1]
            y2 = self.graph[node_id].block.coords[2]
            if node_id != block.node_id and compare_x(x2) and compare_y(y2):
                return node_id
        return gnode_id

    def leaf_selection2(self, block):
        return self.ind_nodes()[0]

    def merkle_hash(self, block):
        hashlist = []
        for predecessor in self.all_downstreams2(block.node_id):
            hashlist.append(hash(self.graph[predecessor].block))
        return BU.hash(tuple(hashlist))

    def add_node_if_not_exists(self, block, graph=None):
        try:
            self.add_node(block)
        except KeyError:
            pass

    def delete_node(self, block, graph=None):
        """ Deletes this node and all edges referencing it. """
        if not graph:
            graph = self.graph
        if block.node_id not in graph:
            raise KeyError('node %s does not exist' % block.node_id)
        graph.pop(block)

        for node, edges in six.iteritems(graph):
            if block.node_id in edges:
                edges.remove(block)

    def delete_node_if_exists(self, block, graph=None):
        try:
            self.delete_node(block, graph=graph)
        except KeyError:
            pass

    def add_edge(self, id1, id2, graph=None):
        """ Add an edge (dependency) between the specified nodes. """
        if not graph:
            graph = self.graph
        if id1 not in graph or id2 not in graph:
            raise KeyError('one or more nodes do not exist in graph')
        test_graph = deepcopy(graph)
        test_graph[id1].edges.append(id2)
        graph[id1].edges.append(id2)
        # is_valid, message = self.validate(test_graph)
        # if is_valid:
        #     graph[id1].edges.append(id2)
        # else:
        #     raise DAGValidationError(message)

    def delete_edge(self, ind_node, dep_node, graph=None):
        """ Delete an edge from the graph. """
        if not graph:
            graph = self.graph
        if dep_node not in graph.get(ind_node, []):
            raise KeyError('this edge does not exist in graph')
        graph[ind_node].remove(dep_node)

    def rename_edges(self, old_task_name, new_task_name, graph=None):
        """ Change references to a task in existing edges. """
        if not graph:
            graph = self.graph
        for node, edges in graph.items():

            if node == old_task_name:
                graph[new_task_name] = copy(edges)
                del graph[old_task_name]

            else:
                if old_task_name in edges:
                    edges.remove(old_task_name)
                    edges.add(new_task_name)

    def predecessors(self, node_id, graph=None):
        """ Returns a list of all predecessors of the given node """
        if graph is None:
            graph = self.graph
        return [key for key in graph if node_id in graph[key].edges]
    
    def all_predecessors(self, node_id, graph=None):
        allpredecessors = []
        if graph is None:
            graph = self.graph
        for nodes in self.predecessors(node_id):
            allpredecessors += [nodes]
            allpredecessors += self.predecessors(nodes, graph)
        return allpredecessors

    def downstream(self, node_id, graph=None):
        """ Returns a list of all nodes this node has edges towards. """
        if graph is None:
            graph = self.graph
        if node_id not in graph:
            raise KeyError('node %s is not in graph' % node_id)
        return list(graph[node_id].edges)

    def all_downstreams2(self, node_id, graph=None):
        alldownstreams = []
        if graph is None:
            graph = self.graph
        for nodes in self.downstream(node_id):
            alldownstreams += [nodes]
            alldownstreams += self.all_downstreams2(nodes, graph)
        return alldownstreams

    def all_downstreams(self, node_id, graph=None):
        """Returns a list of all nodes ultimately downstream
        of the given node in the dependency graph, in
        topological order."""
        if graph is None:
            graph = self.graph
        nodes = [graph[node_id].edges]
        nodes_seen = set()
        i = 0
        while i < len(nodes):
            downstreams = self.downstream(nodes[i], graph)
            for downstream_node in downstreams:
                if downstream_node not in nodes_seen:
                    nodes_seen.add(downstream_node)
                    nodes.append(downstream_node)
            i += 1
        return list(
            filter(
                lambda node: node in nodes_seen,
                self.topological_sort(graph=graph)
            )
        )

    def all_leaves(self, graph=None):
        """ Return a list of all leaves (nodes with no downstreams) """
        if graph is None:
            graph = self.graph
        return [key for key in graph if not graph[key].edges]

    def from_dict(self, graph_dict):
        """ Reset the graph and build it from the passed dictionary.

        The dictionary takes the form of {node_name: [directed edges]}
        """

        self.reset_graph()
        for new_node in six.iterkeys(graph_dict):
            self.add_node(new_node)
        for ind_node, dep_nodes in six.iteritems(graph_dict):
            if not isinstance(dep_nodes, list):
                raise TypeError('dict values must be lists')
            for dep_node in dep_nodes:
                self.add_edge(ind_node, dep_node)

    def ind_nodes(self, graph=None):
        """ Returns a list of all nodes in the graph with no dependencies. """
        if graph is None:
            graph = self.graph

        dependent_nodes = set(
            node for dependents in six.itervalues(graph) for node in dependents.edges
        )
        return [node for node in graph.keys() if node not in dependent_nodes]

    def validate(self, graph=None):
        """ Returns (Boolean, message) of whether DAG is valid. """
        graph = graph if graph is not None else self.graph
        if len(self.ind_nodes(graph)) == 0:
            return (False, 'no independent nodes detected')
        try:
            self.topological_sort(graph)
        except ValueError:
            return (False, 'failed topological sort')
        return (True, 'valid')

    def topological_sort(self, graph=None):
        """ Returns a topological ordering of the DAG.

        Raises an error if this is not possible (graph is not valid).
        """
        if graph is None:
            graph = self.graph

        in_degree = {}
        for u in graph:
            in_degree[u] = 0

        for u in graph:
            for v in graph[u].edges:
                in_degree[v] += 1

        queue = deque()
        for u in in_degree:
            if in_degree[u] == 0:
                queue.appendleft(u)

        l = []
        while queue:
            u = queue.pop()
            l.append(u)
            for v in graph[u].edges:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.appendleft(v)

        if len(l) == len(graph):
            return l
        else:
            raise ValueError('graph is not acyclic')

    def size(self):
        return len(self.graph)
