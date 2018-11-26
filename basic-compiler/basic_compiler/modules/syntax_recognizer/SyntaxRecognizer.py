from basic_compiler.fsm import Fsm, State, Transition
from basic_compiler.modules.EventDrivenModule import EventDrivenModule
from basic_compiler.modules.semantic.llvm import LlvmIrGenerator


class SyntaxRecognizer(EventDrivenModule):
    def open_handler(self, event):
        self.ir_generator = LlvmIrGenerator(event[0])
        exp_fsm = Fsm({})
        exp_fsm.states = {
            'start': State(None, [
                Transition(('special', '+'), 'start'),
                Transition(('special', '-'), 'start', self.ir_generator.negative_expression),
                Transition(None, 'start_expression'),
            ]),
            'start_expression': State(None, [
                Transition(('special', '('), 'nested_expression', self.ir_generator.operator),
                Transition('number', 'end_expression', self.ir_generator.number),
                Transition('variable', 'end_of_variable', self.ir_generator.variable),
                Transition('identifier', 'function_call', self.ir_generator.operator),
            ]),
            'nested_expression': State(None, [
                Transition(exp_fsm, 'end_of_nested_expression', self.ir_generator.end_nested_expression),
            ]),

            'end_of_variable': State(None, [
                Transition(('special', '('), 'variable_dimension'),
                Transition(None, 'end_expression', self.ir_generator.end_of_variable),
            ]),
            'variable_dimension': State(None, [
                Transition(exp_fsm, 'end_of_dimension', self.ir_generator.variable_dimension),
            ]),
            'end_of_dimension': State(None, [
                Transition(('special', ','), 'variable_dimension'),
                Transition(('special', ')'), 'end_expression', self.ir_generator.end_of_variable),
            ]),

            'end_of_nested_expression': State(None, [
                Transition(('special', ')'), 'end_expression'),
            ]),
            'function_call': State(None, [
                Transition(('special', '('), 'nested_expression', self.ir_generator.operator),
            ]),
            'end_expression': State(None, [
                Transition(('special', '+'), 'start_expression', self.ir_generator.operator),
                Transition(('special', '-'), 'start_expression', self.ir_generator.operator),
                Transition(('special', '*'), 'start_expression', self.ir_generator.operator),
                Transition(('special', '/'), 'start_expression', self.ir_generator.operator),
                Transition(('special', '↑'), 'start_expression', self.ir_generator.operator),
                Transition(None, 'accept', self.ir_generator.end_expression),
            ]),
            'accept': State(True)
        }

        self.fsm = Fsm({
            'start': State(None, [
                Transition('number', 'statement', self.ir_generator.label),
                Transition('eof', 'eof', lambda _: print(self.ir_generator.to_ll())),
            ]),

            'statement': State(None, [
                Transition(('identifier', 'LET'), 'let'),
                Transition(('identifier', 'READ'), 'read'),
                Transition(('identifier', 'DATA'), 'data'),
                Transition(('identifier', 'PRINT'), 'print'),
                Transition(('identifier', 'GO'), 'go'),
                Transition(('identifier', 'GOTO'), 'goto'),
                Transition(('identifier', 'IF'), 'if'),
                Transition(('identifier', 'FOR'), 'for'),
                Transition(('identifier', 'NEXT'), 'next'),
                Transition(('identifier', 'DIM'), 'dim'),
                Transition(('identifier', 'DEF'), 'def'),
                Transition(('identifier', 'GOSUB'), 'gosub'),
                Transition(('identifier', 'RETURN'), 'end', self.ir_generator.return_statement),
                Transition(('identifier', 'REM'), 'remark'),
                Transition(('identifier', 'END'), 'end', self.ir_generator.end),
            ]),

            'let': State(None, [
                Transition('variable', 'let_variable_dimensions', self.ir_generator.lvalue),
            ]),
            'let_variable_dimensions': State(None, [
                Transition(('special', '('), 'let_variable_dimension'),
                Transition(None, 'let_assign'),
            ]),
            'let_variable_dimension': State(None, [
                Transition(exp_fsm, 'let_end_of_dimension', self.ir_generator.lvalue_dimension),
            ]),
            'let_end_of_dimension': State(None, [
                Transition(('special', ','), 'let_variable_dimension'),
                Transition(('special', ')'), 'let_assign'),
            ]),
            'let_assign': State(None, [
                Transition(('special', '='), 'let_rvalue', self.ir_generator.lvalue_end),
            ]),
            'let_rvalue': State(None, [
                Transition(exp_fsm, 'end', self.ir_generator.let_rvalue),
            ]),

            'read': State(None, [
                Transition('variable', 'read_variable_dimensions', self.ir_generator.lvalue),
            ]),
            'read_variable_dimensions': State(None, [
                Transition(('special', '('), 'read_variable_dimension'),
                Transition(None, 'end_of_read', self.ir_generator.lvalue_end),
            ]),
            'read_variable_dimension': State(None, [
                Transition(exp_fsm, 'read_end_of_dimension', self.ir_generator.lvalue_dimension),
            ]),
            'read_end_of_dimension': State(None, [
                Transition(('special', ','), 'read_variable_dimension'),
                Transition(('special', ')'), 'end_of_read', self.ir_generator.lvalue_end),
            ]),
            'end_of_read': State(None, [
                Transition(('special', ','), 'read', self.ir_generator.read_item),
                Transition('end_of_line', 'start', self.ir_generator.read_item),
            ]),

            'data': State(None, [
                Transition(('special', '+'), '+data'),
                Transition(('special', '-'), '-data'),
                Transition('number', 'end_of_data', self.ir_generator.data_item),
            ]),
            '+data': State(None, [
                Transition('number', 'end_of_data', self.ir_generator.data_item),
            ]),
            '-data': State(None, [
                Transition('number', 'end_of_data', lambda x: self.ir_generator.data_item('-{}'.format(x))),
            ]),
            'end_of_data': State(None, [
                Transition(('special', ','), 'data'),
                Transition('end_of_line', 'start'),
            ]),

            'print': State(None, [
                Transition('end_of_line', 'start', self.ir_generator.print_newline),
                Transition('string', 'print_after_string', self.ir_generator.print),
                Transition(exp_fsm, 'print_after_exp', self.ir_generator.print_expression_result),
            ]),
            'print_after_string': State(None, [
                Transition(('special', ','), 'print_after_comma'),
                Transition('end_of_line', 'start', self.ir_generator.print_end_with_newline),
                Transition(exp_fsm, 'print_exp_result', self.ir_generator.print_expression_result),
            ]),
            'print_after_comma': State(None, [
                Transition('end_of_line', 'start', self.ir_generator.print_end),
                Transition(exp_fsm, 'print_exp_result'),
            ]),
            'print_after_exp': State(None, [
                Transition(('special', ','), 'print_after_comma'),
                Transition('end_of_line', 'start', self.ir_generator.print_end_with_newline),
            ]),

            'go': State(None, [
                Transition(('identifier', 'TO'), 'goto'),
            ]),
            'goto': State(None, [
                Transition('number', 'end', self.ir_generator.goto),
            ]),

            'if': State(None, [
                Transition(exp_fsm, 'if_operator', self.ir_generator.if_left_exp),
            ]),
            'if_operator': State(None, [
                Transition('special', 'if_right_exp', self.ir_generator.if_operator),
            ]),
            'if_right_exp': State(None, [
                Transition(exp_fsm, 'if_then', self.ir_generator.if_right_exp),
            ]),
            'if_then': State(None, [
                Transition(('identifier', 'THEN'), 'if_target'),
            ]),
            'if_target': State(None, [
                Transition('number', 'end', self.ir_generator.if_target),
            ]),

            'for': State(None, [
                Transition('variable', 'for_=', self.ir_generator.for_variable),
            ]),
            'for_=': State(None, [
                Transition(('special', '='), 'for_left_exp'),
            ]),
            'for_left_exp': State(None, [
                Transition(exp_fsm, 'for_to', self.ir_generator.for_left_exp),
            ]),
            'for_to': State(None, [
                Transition(('identifier', 'TO'), 'for_right_exp'),
            ]),
            'for_right_exp': State(None, [
                Transition(exp_fsm, 'for_step', self.ir_generator.for_right_exp),
            ]),
            'for_step': State(None, [
                Transition(('identifier', 'STEP'), 'for_step_value'),
                Transition('end_of_line', 'start', lambda _: self.ir_generator.for_step_value(1.)),
            ]),
            'for_step_value': State(None, [
                Transition(exp_fsm, 'end', self.ir_generator.for_step_value),
            ]),

            'next': State(None, [
                Transition('variable', 'end', self.ir_generator.next),
            ]),

            'dim': State(None, [
                Transition('variable', 'dim_(', self.ir_generator.lvalue),
            ]),
            'dim_(': State(None, [
                Transition(('special', '('), 'dim_dimensions'),
            ]),
            'dim_dimensions': State(None, [
                Transition('number', 'dim_dimension_end', self.ir_generator.dim_dimension),
            ]),
            'dim_dimension_end': State(None, [
                Transition(('special', ','), 'dim_dimensions'),
                Transition(('special', ')'), 'dim_end', self.ir_generator.dim_end),
            ]),
            'dim_end': State(None, [
                Transition(('special', ','), 'dim'),
                Transition('end_of_line', 'start'),
            ]),

            'def': State(None, [
                Transition('identifier', 'def_(', self.ir_generator.def_identifier),
            ]),
            'def_(': State(None, [
                Transition(('special', '('), 'def_parameter'),
            ]),
            'def_parameter': State(None, [
                Transition('variable', 'def_)', self.ir_generator.def_parameter),
            ]),
            'def_)': State(None, [
                Transition(('special', ')'), 'def_exp'),
            ]),
            'def_exp': State(None, [
                Transition(exp_fsm, 'end', self.ir_generator.def_exp),
            ]),

            'gosub': State(None, [
                Transition('number', 'end', self.ir_generator.gosub),
            ]),
            'remark': State(None, [
                Transition('identifier', 'remark', self.ir_generator.remark),
                Transition('number', 'remark', self.ir_generator.remark),
                Transition('special', 'remark', self.ir_generator.remark),
                Transition('string', 'remark', self.ir_generator.remark),
                Transition('variable', 'remark', self.ir_generator.remark),
                Transition('end_of_line', 'start', self.ir_generator.remark_end),
            ]),
            'end': State(None, [
                Transition('end_of_line', 'start'),
            ]),
            'eof': State('eof')
        })

    def transition_on_event(self, event_name):
        return lambda event: self.fsm.transition((event_name, event[0]))

    def get_handlers(self):
        return {
            'open': self.open_handler,
            **{
                x: self.transition_on_event(x)
                for x in ('end_of_line', 'identifier', 'number', 'special', 'string', 'variable', 'eof')
            },
        }
