import os
from django.conf import settings
from translations.lib.types import (TransManagerMixin, TransManagerError)
from translations.models import POStatistic, Language

# I couldn't import this file from a separated dir
import libpo as po 

class POTStatsError(Exception):

    def __init__(self, lang):
        self.lang = lang

    def __str__(self):
        return "Could not calculate the statistics using the '%s' " \
               "language." % (self.lang)

class POTManager(TransManagerMixin):
    """ A browser class for POT files. """

    def __init__(self, component, file_set, path, source_lang):
        self.component = component
        self.file_set = file_set
        self.path = path
        self.source_lang = source_lang

    def get_po_files(self):
        """ Return a list of PO filenames """

        po_files = []
        for filename in self.file_set:
            if filename.endswith('.po'):
                po_files.append(filename)
        po_files.sort()
        return po_files

    def get_langfile(self, lang):
        """ Return a PO filename """

        for filename in self.get_po_files():
            if os.path.basename(filename[:-3:]) == lang:
                return filename

    def get_langs(self):
        """ Return all langs tha have a po file for a object """

        langs = []
        for filename in self.get_po_files():
            langs.append(os.path.basename(filename[:-3:]))
        langs.sort()
        return langs

    def calcule_stats(self, lang):
        """ 
        Return the statistics of a specificy language for a 
        object 
        """
        try:
            file_path = os.path.join(self.path, self.get_langfile(lang))
            entries = po.read(file_path)
            return po.stats(entries)
        except AttributeError:
            raise POTStatsError, lang

    def create_stats(self, lang):
        """Set the statistics of a specificy language for a object."""
        try:
            stats = self.calcule_stats(lang)
            f = self.get_langfile(lang)
            s = POStatistic.objects.get(object_id=self.component.id, 
                                        filename=f)
        except POTStatsError:
            # TODO: It should probably be raised when a checkout of a 
            # module has a problem. Needs to decide what to do when it
            # happens
            pass
        except POStatistic.DoesNotExist:
            try:
                l = Language.objects.get(code=lang)
            except Language.DoesNotExist:
                l = None
            s = POStatistic.objects.create(lang=l, filename=f, 
                                           object=self.component)
        s.set_stats(trans=stats['translated'], fuzzy=stats['fuzzy'], 
                    untrans=stats['untranslated'])
        return s

    def stats_for_lang_object(self, lang):
        """Return statistics for an object in a specific language."""
        try: 
            return POStatistic.objects.filter(lang=lang, 
                                              object_id=self.component.id)[0]
        except IndexError:
            return None

    def get_stats(self):
        """ Return a list of statistics of languages for an object."""
        return POStatistic.objects.filter(
                   object_id=self.component.id
        ).order_by('-trans_perc')

    def delete_stats_for_object(self, object):
        """ Delete all lang statistics of an object."""
        POStatistic.objects.filter(object_id=object.id).delete()
