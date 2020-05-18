from nltk.stem import PorterStemmer
import json
import os
from builder.layout import description
from nltk.tokenize import word_tokenize
import nltk
import math
from builder.writing_context import WritingContext
from builder.str_tree import StrTree
import builder
from importer.entities import Entity, ClassEntity, PageEntity, ExternalEntity, MemberEntity, GroupEntity, NamespaceEntity
import html2text
from builder.settings import Settings
from builder.page import Page

nltk.download('punkt')
nltk.download('stopwords')


def description_to_string(ctx: WritingContext, node):
    buffer = StrTree()
    description(ctx, node, buffer)
    text = str(buffer)
    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = True
    text_maker.bypass_tables = False
    text_maker.ignore_images = True
    text_maker.ignore_emphasis = True
    text_maker.unicode_snob = True
    return text_maker.handle(text)

class KeywordRanker:
    def __init__(self, ctx: WritingContext, entities):
        occurances = {}
        self.ctx = ctx
        self.stemmer = PorterStemmer()
        self.stop_words = set(nltk.corpus.stopwords.words('english'))
        self.original_words = {}

        for entity in entities:
            self.ctx.page = None
            self.ctx.entity_scope = entity
            # desc1 = description_to_string(self.ctx, entity.briefdescription)
            desc2 = description_to_string(self.ctx, entity.detaileddescription)
            token_words=self.tokenize(desc2)
            for word in token_words:
                stemmed = self.stemmer.stem(word)
                if stemmed not in occurances:
                    occurances[stemmed] = 0
                    self.original_words[stemmed] = word

                occurances[stemmed] += 1
                if len(word) < len(self.original_words[stemmed]):
                    self.original_words[stemmed] = word


        self.occurances = occurances

    def tokenize(self, sentence):
        token_words=word_tokenize(sentence, language="english")
        # Also split by dot
        token_words = [w for word in token_words for w in word.split(".") if w not in self.stop_words]
        return token_words

    def entity_keywords(self, entity):
        self.ctx.page = None
        self.ctx.entity_scope = entity
        desc2 = description_to_string(self.ctx, entity.detaileddescription)

        token_words = self.tokenize(desc2)
        in_document = {}
        for word in token_words:
            stemmed = self.stemmer.stem(word)
            if stemmed not in in_document:
                in_document[stemmed] = 0

            in_document[stemmed] += 1

        keywords = []
        for (word, num_in_document) in in_document.items():
            num_total = self.occurances[word]
            if num_in_document > 1 and len(word) > 1:
                importance = math.log(1 + num_in_document) / math.log(1 + num_total)
                keywords.append((importance, word))

        keywords.sort(reverse=True)
        keywords = keywords[:min(len(keywords), 20)]
        return [self.original_words[x[1]] for x in keywords]

def build_search_data(ctx: WritingContext, entities, settings: Settings) -> None:
    ctx.strip_links = True
    ctx.relpath = lambda p: ""

    ranker = KeywordRanker(ctx, entities)

    search_items = []
    for i, ent in enumerate(entities):
        if isinstance(ent, ClassEntity):
            search_items.append({
                "url": ent.path.full_url(),
                "name": ent.name,
                "fullname": ent.name,
                "boost": search_boost(None, ent),
                "keys": [],
                "type": "class",
            })

            for m in ent.all_members:
                assert(isinstance(m, MemberEntity))
                if m.name == ent.name:
                    # Probably a constructor. Ignore those in the search results
                    continue

                if m.defined_in_entity != ent:
                    # Inherited member, ignore in search results
                    continue

                search_item = {
                    "url": m.path.full_url(),
                    "name": m.name,
                    "fullname": search_full_name(ctx, ent, m),
                    "boost": search_boost(ent, m),
                    "keys": [],
                    "type": "member",
                }
                search_items.append(search_item)

        if isinstance(ent, PageEntity):
            search_items.append({
                "url": ent.path.full_url(),
                "name": ent.name,
                "fullname": ent.name,
                "boost": search_boost(None, ent),
                "keys": ranker.entity_keywords(ent),
                "type": "page",
            })

        if isinstance(ent, GroupEntity):
            search_items.append({
                "url": ent.path.full_url(),
                "name": ent.name,
                "fullname": ent.name,
                "boost": search_boost(None, ent),
                "keys": [],
                "type": "group",
            })

    f = open(os.path.join(settings.out_dir, "search_data.json"), "w")
    f.write(json.dumps(search_items))
    f.close()

    ctx.strip_links = False
    ctx.relpath = None

def search_full_name(ctx: WritingContext, parent: ClassEntity, ent: MemberEntity) -> str:
    result = parent.name + "." + ent.name
    ctx = ctx.with_link_stripping()

    if ent.hasparams:
        params = []
        for param in ent.params:
            buffer = StrTree()
            builder.layout.markup(ctx, param.type, buffer)
            params.append(str(buffer).replace(" ", ""))

        result += "(" + ",".join(params) + ")"
    return result

def search_boost(parent: Entity, ent: Entity) -> float:
    boost = 100.0
    if isinstance(ent, ClassEntity):
        boost *= 2.0
    elif isinstance(ent, NamespaceEntity):
        boost *= 1.5
    elif isinstance(ent, PageEntity):
        boost *= 2.0
    elif isinstance(ent, ExternalEntity):
        boost *= 0.5

    if hasattr(ent, "protection"):
        if ent.protection == "private":
            boost *= 0.5
        elif ent.protection == "package":
            boost *= 0.6
        elif ent.protection == "protected":
            boost *= 0.8

    return math.log(boost)
