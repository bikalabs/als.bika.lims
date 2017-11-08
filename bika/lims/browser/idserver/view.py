from bika.lims.browser import BrowserView
from bika.lims.numbergenerator import INumberGenerator
from zope.component import getUtility


class IDServerView(BrowserView):

    def seed(self):
        """ You seed at 100, object added will start at 101
        """
        form = self.request.form
        prefix = form.get('prefix', None)
        if prefix is None:
            return 'No prefix provided'
        seed = form.get('seed', None)
        if seed is None:
            return 'No seed provided'

        seed = int(seed) - 1
        number_generator = getUtility(INumberGenerator)
        new_seq = number_generator.set_seed(key=prefix, seed=seed)
        return 'IDServerView: "%s" seeded to %s' % (prefix, new_seq)
