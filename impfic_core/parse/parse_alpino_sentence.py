from typing import Dict, Generator, List, Union

import json

SENT_TAGS = {'smain', 'ssub', 'svan', 'sv1'}
MAIN_VERBAL_TAGS = {'smain', 'ssub', 'svan', 'sv1', 'inf', 'ti', 'oti', 'ppart', 'ppres'}

MAIN_COMPLEMENT_TAGS = {'hd', 'su', 'sup', 'obj1', 'pobj1', 'se', 'obj2', 'predc', 'vc', 'pc',
                        'me', 'ld', 'svp'}


def invert_tree(curr_node: Dict[str, any], inverse_tree: Dict[int, int],
                nodes: Dict[int, Dict[str, any]]) -> None:
    """Fill an inverse tree and dictionary of node IDs and nodes for a given node."""
    if "node" not in curr_node:
        nodes[curr_node["@id"]] = curr_node
    elif isinstance(curr_node["node"], list):
        for child_node in curr_node["node"]:
            inverse_tree[child_node["@id"]] = curr_node["@id"]
            nodes[child_node["@id"]] = child_node
            invert_tree(child_node, inverse_tree, nodes)
    elif isinstance(curr_node["node"], dict):
        # print(curr_node)
        inverse_tree[curr_node["node"]["@id"]] = curr_node["@id"]
        invert_tree(curr_node["node"], inverse_tree, nodes)
    nodes[curr_node['@id']] = curr_node


def get_word_nodes(curr_node: Dict[str, any]):
    """Return all descendants nodes that have '@word' property for a given node."""
    word_nodes = []
    if "@word" in curr_node:
        return [curr_node]
    elif "node" not in curr_node:
        return []
    elif isinstance(curr_node["node"], list):
        for child_node in curr_node["node"]:
            child_words = get_word_nodes(child_node)
            word_nodes += child_words
    elif isinstance(curr_node["node"], dict):
        child_node = curr_node["node"]
        word_nodes += get_word_nodes(child_node)
    else:
        print(curr_node)
        raise TypeError("Unknown node type")
    return word_nodes


def parse_tree(sent: Dict[str, any]):
    """Return the node tree, the inverse node tree and a node ID -> node dictionary
    for a given Elasticsearch-indexed alpino sentence."""
    tree = json.loads(sent["alpino_ds"])
    root = tree["node"]
    inverse_tree = {}
    nodes = {}
    invert_tree(root, inverse_tree, nodes)
    return tree, inverse_tree, nodes


def get_nodes_by_tag(tag: str, nodes: Dict[int, Dict[str, any]]) -> List[Dict[str, any]]:
    """Return all nodes that contain a given tag. Tags are looked up in properties
    cat, lcat, pos and pt"""
    tag_nodes = []
    for node_id in nodes:
        node = nodes[node_id]
        if '@rel' in node and node['@rel'] == tag:
            tag_nodes.append(node)
        if '@cat' in node and node['@cat'] == tag:
            tag_nodes.append(node)
        if '@lcat' in node and node['@lcat'] == tag:
            tag_nodes.append(node)
        if '@pos' in node and node['@pos'] == tag:
            tag_nodes.append(node)
        if '@pt' in node and node['@pt'] == tag:
            tag_nodes.append(node)
    return tag_nodes


def is_descendant_of(node1, node2, nodes, inverse_tree):
    if node1 == node2:
        return False
    if node1['@id'] not in inverse_tree:
        return False
    parent = nodes[inverse_tree[node1['@id']]]
    while parent and parent['@id'] in inverse_tree:
        parent = nodes[inverse_tree[parent['@id']]]
        if parent == node2:
            break
    return parent == node2


def is_ancestor_of(node1, node2, nodes, inverse_tree):
    return is_descendant_of(node2, node1, nodes, inverse_tree)


def is_sent_node(node: Dict[str, any]) -> bool:
    """Check if node is a main verbal complement."""
    if node is None:
        return False
    return '@cat' in node and node['@cat'] in SENT_TAGS


def is_main_verbal(node: Dict[str, any]) -> bool:
    """Check if node is a main verbal complement."""
    if node is None:
        return False
    return '@cat' in node and node['@cat'] in MAIN_VERBAL_TAGS


def is_verbal(node: Dict[str, any]) -> bool:
    """Check if a node is a verbal complement (verb complement or main verbal complement)."""
    if node is None:
        return False
    return node['@rel'] == 'vc' or is_main_verbal(node)


def is_finite_verb(node: Dict[str, any]) -> bool:
    """Check if a node is a finite verb."""
    if node is None:
        return False
    return '@wvorm' in node and node['@wvorm'] == 'pv'


def is_reference_node(node: Dict[str, any]) -> bool:
    """Check if a node nas no lexical content but references another node."""
    if node is None:
        return False
    return '@index' in node and '@word' not in node and '@cat' not in node


def is_referent_node(node: Dict[str, any], ref_node: Dict[str, any]) -> bool:
    """Check if a given node is the referent of a given reference node"""
    if node is None or ref_node is None:
        return False
    if '@index' in node and '@word' in node and node['@index'] == ref_node['@index']:
        return True
    elif '@index' in node and '@cat' in node and node['@index'] == ref_node['@index']:
        return True
    else:
        return False


def is_pronoun(node):
    """Check if a given node is a pronoun."""
    return '@persoon' in node or 'pron' in node['@frame']


def is_personal_pronoun(node):
    """Check if a given node is a personal pronoun."""
    return '@persoon' in node


def is_possessive_pronoun(node):
    """Check if a given node is a possessive pronoun."""
    return is_personal_pronoun(node) and '@vwtype' in node and node['@vwtype'] == 'bez'


def is_accusative_pronoun(node):
    """Check if a given node is a accusative pronoun."""
    return is_personal_pronoun(node) and '@case' in node and node['@case'] == 'dat_acc'


def get_referent_node(ref_node: Dict[str, any],
                      nodes: Dict[int, Dict[str, any]]) -> Union[None, Dict[str, any]]:
    """Return the referent node for a given reference node."""
    for node_id in nodes:
        node = nodes[node_id]
        if is_referent_node(node, ref_node):
            return node
    return None


def get_personal_pronouns(nodes: Dict[int, Dict[str, any]]) -> List[Dict[str, any]]:
    """Return all personal pronouns nodes for a given sentence-like node."""
    return [nodes[node_id] for node_id in nodes if is_personal_pronoun(nodes[node_id])]


def get_possessive_pronouns(nodes: Dict[int, Dict[str, any]]) -> List[Dict[str, any]]:
    """Return all possessive pronouns nodes for a given sentence-like node."""
    return [nodes[node_id] for node_id in nodes if is_possessive_pronoun(nodes[node_id])]


def get_accusative_pronouns(nodes: Dict[int, Dict[str, any]]) -> List[Dict[str, any]]:
    """Return all accusative pronouns nodes for a given sentence-like node."""
    return [nodes[node_id] for node_id in nodes if is_accusative_pronoun(nodes[node_id])]


def get_descendants(node: Dict[str, any]) -> List[Dict[str, any]]:
    """Get all descendant nodes for a given node."""
    if 'node' not in node:
        return []
    descendants = [n for n in node['node']]
    for child in node['node']:
        descendants += get_descendants(child)
    return descendants


def get_descendant_words(node: Dict[str, any], nodes: Dict[int, Dict[str, any]]) -> List[Dict[str, any]]:
    """Return a list of nodes that are descendants of a given node."""
    if is_reference_node(node):
        for node_id in nodes:
            n = nodes[node_id]
            if is_referent_node(n, node):
                node = n
                break
    if '@word' in node:
        return [node]
    if 'node' not in node:
        return []
    else:
        return [n for n in get_descendants(node) if '@word' in n]


def get_subject(node: Dict[str, any], nodes: Dict[int, Dict[str, any]]) -> Union[None, Dict[str, any]]:
    """Return the subject node that is part of a given sentence node."""
    sub_node = None
    # First find the node with the relation 'su' (subject)
    # It's either the node itself or one of it's direct children
    if node['@rel'] == 'su':
        sub_node = node
    elif 'node' in node:
        for child in node['node']:
            if child['@rel'] == 'su':
                sub_node = child
    # Second, check if the node is a reference node and
    # if so, find it's referent node
    if sub_node and is_reference_node(sub_node):
        sub_node = get_referent_node(sub_node, nodes)
    return sub_node


def get_direct_object(node: Dict[str, any], nodes: Dict[int, Dict[str, any]]) -> Union[None, Dict[str, any]]:
    """Return the direct object that is part of a given sentence node
    (or the predicative complement if there is no direct object)"""
    obj_node = None
    # First find the node with the relation obj1 (direct object) or 'predc' (predicative complement)
    # It's either the node itself or one of it's direct children
    if node['@rel'].startswith('obj') or node['@rel'] == 'predc':
        obj_node = node
    elif 'node' in node:
        for child in node['node']:
            if child['@rel'] == 'obj1':
                obj_node = child
                break
        if obj_node is None:
            # if there is no explicit direct object, look for a predicate complement
            for child in node['node']:
                if child['@rel'] == 'predc':
                    obj_node = child
                    break
        if obj_node is None:
            # there is no direct obj or pred. complement, so look for a verb clause that
            # may contain an object
            for child in node['node']:
                if is_main_verbal(child) or child['@rel'] == 'pc':
                    descendants = get_descendants(child)
                    for desc in descendants:
                        if desc['@rel'] == 'obj1':
                            obj_node = desc
                            break
                    if obj_node is None:
                        # if there is no explicit direct object, look for a predicate complement
                        for desc in descendants:
                            if desc['@rel'] == 'predc':
                                obj_node = desc
                                break
                    break
    # Second, check if the node is a reference node and
    # if so, find it's referent node
    if obj_node is not None and is_reference_node(obj_node):
        obj_node = get_referent_node(obj_node, nodes)
    return obj_node


def get_indirect_object(node: Dict[str, any], nodes: Dict[int, Dict[str, any]]) -> Union[None, Dict[str, any]]:
    """Return the indirect object (obj2) that is part of a given sentence node."""
    obj_node = None
    # First find the node with the relation obj2 (indirect object)
    # It's either the node itself or one of it's direct children
    if node['@rel'] == ['obj2']:
        obj_node = node
    elif 'node' in node:
        for child in node['node']:
            if child['@rel'] == 'obj2':
                obj_node = child
                break
        if obj_node is None:
            # there is no direct obj or pred. complement, so look for a verb clause that
            # may contain an object
            for child in node['node']:
                if is_main_verbal(child):
                    descendants = get_descendants(child)
                    for desc in descendants:
                        if desc['@rel'] == 'obj2':
                            obj_node = desc
                            break
                    break
    # Second, check if the node is a reference node and
    # if so, find it's referent node
    if obj_node is not None and is_reference_node(obj_node):
        obj_node = get_referent_node(obj_node, nodes)
    return obj_node


def get_relative_head_referent(node: Dict[str, any], nodes: Dict[int, Dict[str, any]],
                               inverse_tree: Dict[int, int]) -> Union[None, Dict[str, any]]:
    """Return the referent node for a given relative head node."""
    if node['@rel'] != 'rhd':
        return None
    # parent = nodes[inverse_tree[node['@id']]]
    parent = node
    phrase_types = {'np', 'ap'}
    while parent is not None and parent['@cat'] not in phrase_types and parent['@id'] in inverse_tree:
        parent = nodes[inverse_tree[parent['@id']]]
    if parent and parent['@cat'] in phrase_types:
        return parent
    else:
        return None


def get_finite_verb(node: Dict[str, any]) -> Dict[str, any]:
    """Return the finite verb (wvorm=pv) that is part of a given sentence node."""
    fin_verb = None
    # Find the node with the relation 'su' (subject)
    # It's either the node itself or one of it's direct children
    if is_finite_verb(node):
        fin_verb = node
    elif 'node' in node:
        for child in node['node']:
            if is_finite_verb(child):
                fin_verb = child
    return fin_verb


def get_node_sent_parent(node: Dict[str, any], nodes: Dict[int, Dict[str, any]],
                         inverse_tree: Dict[int, int]) -> Union[None, Dict[str, any]]:
    """Return the most direct sentence-like ancestor node of a given node."""
    parent = None
    if node['@id'] not in inverse_tree:
        return parent
    parent = nodes[inverse_tree[node['@id']]]

    while parent and not is_sent_node(parent) and parent['@id'] in inverse_tree:
        parent = nodes[inverse_tree[parent['@id']]]
    return parent if is_sent_node(parent) else None


def get_sent_verbs(node: Dict[str, any]) -> List[Dict[str, any]]:
    """Return a list of all verbs that belong directly under the sentence.
    Verbs in lower sentence-like nodes are ignored."""
    sent_verbs = []
    if 'node' in node:
        for child in node['node']:
            if '@word' in child and child['@pos'] == 'verb':
                sent_verbs.append(child)
            elif is_sent_node(child):
                # child is a sentence-like node, so ignore
                continue
            elif 'node' in child:
                sent_verbs += get_sent_verbs(child)
    elif '@word' in node and node['@pos'] == 'verb':
        sent_verbs.append(node)
    return sent_verbs


def get_main_verb(node: Dict[str, any]) -> Union[None, Dict[str, any]]:
    """Return the main verb node for a given sentence node."""
    # print('GETTING MAIN VERB', node['@id'], node['@cat'])
    main_verb = None
    head_verb = None
    if '@word' in node and node['pos'] == 'verb' and node['@rel'] == 'hd':
        main_verb = node
        head_verb = node
    elif '@cat' in node and node['@rel'] == 'vc':
        main_verb = node
    elif 'node' in node:
        for child in node['node']:
            # if '@cat' in child or '@word' in child:
            #    print('\tCHILD:', child['@rel'], child['@cat'] if '@cat' in child else child['@word'])
            if '@word' in child and child['@pos'] == 'verb' and child['@rel'] == 'hd':
                if main_verb is None:
                    # only use the hd verb if no vc is found (yet)
                    main_verb = child
                    head_verb = child
            elif is_main_verbal(child):
                main_verb = child
    # if main_verb:
    #     print('MAIN VERB NODE:', main_verb['@id'], main_verb['@rel'],
    #           main_verb['@cat'] if '@cat' in main_verb else main_verb['@word'])

    if main_verb is not None and is_verbal(main_verb):
        node = main_verb
        main_verb = None
        # print('HEAD VERB IS:', head_verb['@word'] if head_verb else None)
        # print('MAIN VERB IS VC')
        for child in node['node']:
            # print('\tVC CHILD:', child['@id'], child['@rel'], child['@word'] if '@word' in child else None)
            if '@word' in child and child['@pos'] == 'verb' and child['@rel'] == 'hd':
                main_verb = child
                break
        if main_verb is None:
            for child in node['node']:
                if child and '@cat' in child and child['@cat'] in MAIN_VERBAL_TAGS:
                    main_verb = get_main_verb(child)
    if main_verb and '@word' not in main_verb and head_verb is not None:
        # print('RESTORING HEAD VERB TO MAIN VERB')
        main_verb = head_verb
    return main_verb


def get_node_words(node: Dict[str, any], nodes: Dict[int, Dict[str, any]],
                   inverse_tree: Dict[int, int]) -> Union[None, str]:
    """Return the string of words that are part of a node."""
    word_nodes = []
    if node is None:
        return None
    elif '@word' in node:
        return node['@word']
    elif node['@rel'] == 'rhd':
        rhead = get_relative_head_referent(node, nodes, inverse_tree)
        if rhead:
            word_nodes = [n for n in rhead['node'] if '@word' in n]
        else:
            print('REL HEAD REF:', node['@cat'], node['@id'])
            raise TypeError('No referent with appropriate phrase type found')
    elif 'node' in node:
        word_nodes = [n for n in get_descendant_words(node, nodes) if '@word' in n]
    return ' '.join([n['@word'] for n in sorted(word_nodes, key=lambda x: x['@begin'])])


def get_sent_nodes(nodes: Dict[int, Dict[str, any]]) -> Union[None, Generator[Dict[str, any], None, None]]:
    """Return all nodes that have a sentence type as category from a given list of nodes"""
    for node_id in nodes:
        node = nodes[node_id]
        if '@cat' in node and node['@cat'] in SENT_TAGS:
            yield node
    return None


def get_main_verbal_nodes(nodes: Dict[int, Dict[str, any]]) -> Union[None, Generator[Dict[str, any], None, None]]:
    """Return all nodes that have a sentence type as category from a given list of nodes"""
    for node_id in nodes:
        node = nodes[node_id]
        if '@cat' in node and node['@cat'] in MAIN_VERBAL_TAGS:
            yield node
    return None


def get_node_tag(node: Dict[str, any]) -> Union[None, str]:
    """Return the tag (pos for lexical nodes or cat for frase nodes"""
    if node:
        return node['@pos'] if '@word' in node else node['@cat']
    else:
        return None


def get_sent_node_main_elements(nodes: Dict[int, Dict[str, any]]) -> List[Dict[str, any]]:
    main_elements = []
    for main_verbal_node in get_main_verbal_nodes(nodes):
        verbal_elements = get_verbal_node_main_elements(main_verbal_node, nodes)
        main_elements.append(verbal_elements)
    return main_elements


def get_verbal_node_main_elements(main_verbal_node, nodes: Dict[int, Dict[str, any]]) -> Dict[str, any]:
    return {
        "verbal_node": main_verbal_node,
        "subject": get_subject(main_verbal_node, nodes),
        "direct_object": get_direct_object(main_verbal_node, nodes),
        "indirect_object": get_indirect_object(main_verbal_node, nodes),
        "finite_verb": get_finite_verb(main_verbal_node),
        "main_verb": get_main_verb(main_verbal_node),
        "verb_nodes": get_sent_verbs(main_verbal_node)
    }


def print_sent_main_elements(tree: Dict[str, Dict[str, any]],
                             inverse_tree: Dict[int, int],
                             nodes: Dict[int, Dict[str, any]]):
    print(tree['sentence']['#text'])
    print('\n')
    main_elements = get_sent_node_main_elements(nodes)
    for verbal_elements in main_elements:
        sent_node = verbal_elements['verbal_node']
        words = get_node_words(sent_node, nodes, inverse_tree)
        print(sent_node['@id'], sent_node['@begin'], sent_node['@end'], sent_node['@cat'], sent_node['@rel'], words)
        sub_words = get_node_words(verbal_elements["subject"], nodes, inverse_tree)
        sub_tag = get_node_tag(verbal_elements["subject"])
        obj1 = verbal_elements["direct_object"]
        obj2 = verbal_elements["indirect_object"]
        obj1_words = get_node_words(obj1, nodes, inverse_tree)
        obj2_words = get_node_words(obj2, nodes, inverse_tree)
        obj1_tag = get_node_tag(verbal_elements["direct_object"])
        obj2_tag = get_node_tag(verbal_elements["indirect_object"])
        sub_id = verbal_elements["subject"]['@id'] if verbal_elements["subject"] else None
        print(f"\t{'subject: ': <15}{sub_id}\t{sub_tag}\t{sub_words}")
        if verbal_elements['finite_verb']:
            fin_verb = verbal_elements["finite_verb"]
            print(f"\t{'finite verb: ': <15}{fin_verb['@id']}\t{fin_verb['@rel']}\t{fin_verb['@word']}")
        if verbal_elements['main_verb']:
            main_verb = verbal_elements['main_verb']
            if '@word' not in main_verb:
                print(main_verb)
            print(f"\t{'main verb: ': <15}{main_verb['@id']}\t{main_verb['@rel']}\t{main_verb['@word']}")
        verb_words = [n['@word'] for n in verbal_elements["verb_nodes"]]
        print(f"\t{'verbs: ': <15}", verb_words)
        print(f"\t{'direct object: ': <15}{obj1['@id'] if obj1 else None}\t{obj1_tag}\t{obj1_words}")
        print(f"\t{'indirect object: ': <15}{obj2['@id'] if obj2 else None}\t{obj2_tag}\t{obj2_words}")
