from fontFeatures.shaperLib.Buffer import Buffer, BufferItem, _add_value_records
import weakref


class VariationAwareBufferItem(BufferItem):
    def prep_glyph(self, font):
        super().prep_glyph(font)
        # # Interpolate width
        if not hasattr(self.buffer(), "vf"):
            return
        vf = self.buffer().vf
        if vf:
            glyphs = [vf.masters[master][self.glyph] for master in vf.master_order]
            widthset = {vf.master_order[i]: glyphs[i].width for i in range(len(vf.masters))}
            self.position.xAdvance = vf.interpolate_tuples(widthset, self.buffer().location)

    @classmethod
    def new_unicode(klass, codepoint, buffer=None):
        self = klass()
        self.codepoint = codepoint
        self.glyph = None
        self.feature_masks = {}
        self.buffer = weakref.ref(buffer)
        return self

    @classmethod
    def new_glyph(klass, glyph, font, buffer=None):
        self = klass()
        self.codepoint = None
        self.glyph = glyph
        self.buffer = weakref.ref(buffer)
        self.feature_masks = {}
        self.prep_glyph(font)
        return self

    def add_position(self, vr2):
        if not hasattr(self.buffer(), "vf"):
            return super().add_position(vr2)
        vf = self.buffer().vf
        if vf:
            vr2 = vr2.get_value_for_location(vf, self.buffer().location)
        _add_value_records(self.position, vr2)

class VariationAwareBuffer(Buffer):
    itemclass = VariationAwareBufferItem

    def store_glyphs(self, glyphs):
        self.items = [self.itemclass.new_glyph(g, self.font, self) for g in glyphs]

    def store_unicode(self, unistring):
        self.items = [self.itemclass.new_unicode(ord(char), self) for char in unistring ]
