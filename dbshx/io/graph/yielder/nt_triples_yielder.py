from dbshx.utils.log import log_to_error
from dbshx.utils.uri import there_is_arroba_after_last_quotes
from dbshx.utils.triple_yielders import tune_prop, tune_token, check_if_property_belongs_to_namespace_list
from dbshx.io.graph.yielder.base_triples_yielder import BaseTriplesYielder


class NtTriplesYielder(BaseTriplesYielder):

    def __init__(self, source_file=None, namespaces_to_ignore=None, allow_untyped_numbers=False, raw_graph=None):

        super(NtTriplesYielder, self).__init__()
        self._source_file = source_file
        self._raw_graph = raw_graph
        self._triples_count = 0
        self._error_triples = 0
        self._namespaces_to_ignore = namespaces_to_ignore
        self._allow_untyped_numbers = allow_untyped_numbers
        self._line_reader = self._decide_line_reader()
        # The following ones are refs to functions. Im avoiding some comparison here.
        self.yield_triples = self._yield_triples_not_excluding_namespaces if namespaces_to_ignore is None \
            else self._yield_triples_excluding_namespaces

    def _yield_triples_excluding_namespaces(self):
        self._reset_count()
        for a_line in self._line_reader.read_lines():
            tokens = self._look_for_tokens(a_line.strip())
            if len(tokens) != 3:
                self._error_triples += 1
                log_to_error(msg="This line caused error: " + a_line,
                             source=self._source_file)
            else:
                candidate_triple = (tune_token(tokens[0]),
                                    tune_prop(tokens[1]),
                                    tune_token(tokens[2], allow_untyped_numbers=self._allow_untyped_numbers))
                if not check_if_property_belongs_to_namespace_list(str(candidate_triple[1]),
                                                                   self._namespaces_to_ignore):
                    yield candidate_triple
                self._triples_count += 1

    def _yield_triples_not_excluding_namespaces(self):
        self._reset_count()
        for a_line in self._line_reader.read_lines():
            tokens = self._look_for_tokens(a_line.strip())
            if len(tokens) != 3:
                self._error_triples += 1
                log_to_error(msg="This line caused error: " + a_line,
                             source=self._source_file)
            else:
                yield (tune_token(tokens[0]), tune_prop(tokens[1]), tune_token(tokens[2]))
                self._triples_count += 1

    def _look_for_tokens(self, str_line):
        result = []
        current_first_index = 0
        while current_first_index != len(str_line):
            if str_line[current_first_index] == "<":
                last_index = self._look_for_last_index_of_uri_token(str_line, current_first_index)
                result.append(str_line[current_first_index:last_index + 1])
                current_first_index = last_index + 1
            elif str_line[current_first_index] == '"':
                last_index = self._look_for_last_index_of_literal_token(str_line, current_first_index)
                result.append(str_line[current_first_index:last_index + 1])
                current_first_index = last_index + 1
            elif str_line[current_first_index] == '.':

                break
            else:
                current_first_index += 1

        return result

    def _look_for_last_index_of_uri_token(self, target_str, first_index):
        target_substring = target_str[first_index:]
        index_sub = target_substring.find(">")
        return index_sub + (len(target_str) - len(target_substring))

    def _look_for_last_index_of_literal_token(self, target_str, first_index):
        target_substring = target_str[first_index:]

        if there_is_arroba_after_last_quotes(target_substring):  # String labelled with language
            return target_substring[target_substring.rfind("@"):].find(" ") - 1 + target_str.rfind("@")
        elif "^^" not in target_substring:  # Not typed
            success = False
            index_of_quotes = 1
            while not success:
                index_of_second_quotes = target_substring[index_of_quotes + 1:].find('"') + index_of_quotes + 1
                if target_substring[index_of_second_quotes - 1] != "\\":
                    success = True
                elif target_substring[index_of_second_quotes - 2] == "\\":  # Case of escaped slash "\\"
                    success = True
                index_of_quotes = index_of_second_quotes
            return index_of_quotes + (len(target_str) - len(target_substring))
        else:  # Typed
            return target_substring[target_substring.find("^^"):].find(" ") - 1 + target_str.find("^^")

    @property
    def yielded_triples(self):
        return self._triples_count

    @property
    def error_triples(self):
        return self._error_triples

    def _reset_count(self):
        self._error_triples = 0
        self._triples_count = 0
