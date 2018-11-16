class SemanticError(RuntimeError):
    pass


class Function:
    def __init__(self, name, arguments='', attributes='#0'):
        self.name = name
        self.arguments = arguments
        self.attributes = attributes
        self.instructions = []

    def append(instruction):
        self.instructions.append(instruction)

    def to_ll():
        return '\n'.join((
            'define dso_local i32 @{}({}) local_unnamed_addr {} {'.format(self.name, self.arguments, self.attributes),
            '\n'.join(('  {}'.format(x) for x in self.instructions)),
            '}',
        ))


class Llvm:
    def __init__(self, filename):
        self.filename = filename

        program = Function('program', 'i8* %target_label', '#0')
        program.append('entry:')
        main = Function('main', attributes='#1')
        main.append('tail call void @program(blockaddress(@program, %entry)) #0')
        main.append('ret i32 0')
        self.functions = [program, main]

        self.referenced_functions = set()
        self.defined_labels = set()
        self.referenced_labels = set()
        self.call_targets = {'entry'}

    def label(self, identifier):
        self.defined_labels.add(identifier)
        self.functions[0].append('  label_{}:'.format(identifier))

    def goto(self, target):
        self.referenced_labels.add(target)
        self.functions[0].append('  br label %label_{}'.format(target))

    def def_statement(self, potato):  # TODO
        pass

    def gosub(self, target):
        self.referenced_labels.add(target)
        self.call_targets.add(target)
        self.functions[0].append('  tail call void %label_{}()'.format(target))

    def return_statement(self):
        self.functions[0].append('  ret void')

    def remark(self, text):
        self.functions[0].append('  ; {}'.format(text))

    def end(self, event):
        self.functions[0].append('  tail call void @exit(i32 0) noreturn nounwind')

    def to_ll(self):
        defined_functions = {x.name for x in self.functions}
        undefined_functions = self.referenced_functions - defined_functions
        if undefined_functions:
            raise SemanticError('Undefined functions: {}'.format(undefined_functions))

        undefined_labels = self.referenced_labels - self.defined_labels
        if undefined_labels:
            raise SemanticError('Undefined labels: {}'.format(undefined_labels))

        call_label_list = ', '.join(('label %{}'.format(x) for x in self.call_targets))
        self.functions[0].instructions.insert(0, 'indirectbr i8* %target_label, [ {} ])'.format(call_label_list))

        return '\n'.join((
            'source_filename = {}'.format(self.filename),
            '\n'.join(x.to_ll() for x in self.functions),
            '''declare void @exit(i32) local_unnamed_addr noreturn nounwind

attributes #0 = { nounwind "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="true" "no-jump-tables"="false" "no-nans-fp-math"="true" "no-signed-zeros-fp-math"="true" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="true" "use-soft-float"="false" }
attributes #1 = { norecurse nounwind "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="false" "no-infs-fp-math"="true" "no-jump-tables"="false" "no-nans-fp-math"="true" "no-signed-zeros-fp-math"="true" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="true" "use-soft-float"="false" }

!llvm.ident = !{!0}
!0 = !{!"BASIC to LLVM IR compiler (https://github.com/tiagoshibata/pcs3866-compilers)"}'''
        ))