class Seq:
    def __init__(self, strbase):

        self.strbase = strbase

    def len(self):

        return len(self.strbase)

    def complement(self):

        bases_comp = dict(zip(['A', 'C', 'G', 'T'], ['T', 'G', 'C', 'A']))

        comp = []

        for i in self.strbase:
             if i in bases_comp.keys():
                 comp.append(bases_comp[i])

        comp = ''.join(comp)

        return Seq(comp)

    def reverse(self):

        return Seq(self.complement().strbase[::-1])

    def count(self, base):

        return self.strbase.count(base)

    def perc(self, base):

        return round(100.0 * self.count(base) / self.len(), 1)
