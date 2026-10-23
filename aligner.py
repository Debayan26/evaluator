# aligner.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def get_text_items(classified_document):
    """
    Select text-based items from the classified document
    for alignment.
    """

    return [
        item
        for item in classified_document["content"]
        if item["content_type"] in [
            "text",
            "numeric_fact"
        ]
        and item.get("text")
    ]


class ContentAligner:

    def align_text(
        self,
        source_items,
        ai_items,
        threshold=0.30
    ):
        """
        Align source content with AI-generated content.

        Returns:
        - matched
        - missing
        - extra
        """

        if not source_items:
            return {
                "matched": [],
                "missing": [],
                "extra": ai_items
            }

        if not ai_items:
            return {
                "matched": [],
                "missing": source_items,
                "extra": []
            }

        source_texts = [
            item["text"]
            for item in source_items
        ]

        ai_texts = [
            item["text"]
            for item in ai_items
        ]

        # Combine both documents so TF-IDF uses
        # the same vocabulary.
        all_texts = source_texts + ai_texts

        vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2)
        )

        vectors = vectorizer.fit_transform(all_texts)

        source_vectors = vectors[:len(source_texts)]

        ai_vectors = vectors[len(source_texts):]

        similarity_matrix = cosine_similarity(
            source_vectors,
            ai_vectors
        )

        matched = []
        missing = []

        used_ai = set()

        for source_index, source_item in enumerate(source_items):

            best_ai_index = None
            best_score = -1

            for ai_index in range(len(ai_items)):

                # Avoid matching one AI paragraph
                # with multiple source paragraphs.
                if ai_index in used_ai:
                    continue

                score = similarity_matrix[
                    source_index,
                    ai_index
                ]

                if score > best_score:
                    best_score = score
                    best_ai_index = ai_index

            if (
                best_ai_index is not None
                and best_score >= threshold
            ):

                matched.append({
                    "source": source_item,
                    "ai": ai_items[best_ai_index],
                    "alignment_score": round(
                        float(best_score),
                        4
                    )
                })

                used_ai.add(best_ai_index)

            else:
                missing.append(source_item)

        extra = [
            item
            for index, item in enumerate(ai_items)
            if index not in used_ai
        ]

        return {
            "matched": matched,
            "missing": missing,
            "extra": extra
        }


'''
import numpy as np
from sentence_transformers import SentenceTransformer


class ContentAligner:

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def align_text(
        self,
        source_items,
        ai_items,
        threshold=0.65
    ):

        if not source_items:
            return {
                "matched": [],
                "missing": [],
                "extra": ai_items
            }

        if not ai_items:
            return {
                "matched": [],
                "missing": source_items,
                "extra": []
            }

        source_texts = [
            item["text"]
            for item in source_items
        ]

        ai_texts = [
            item["text"]
            for item in ai_items
        ]

        source_embeddings = self.model.encode(
            source_texts,
            normalize_embeddings=True
        )

        ai_embeddings = self.model.encode(
            ai_texts,
            normalize_embeddings=True
        )

        similarity_matrix = np.matmul(
            source_embeddings,
            ai_embeddings.T
        )

        matched = []
        missing = []
        used_ai = set()

        for source_index, source_item in enumerate(source_items):

            scores = similarity_matrix[source_index].copy()

            for ai_index in used_ai:
                scores[ai_index] = -1

            best_ai_index = int(np.argmax(scores))
            best_score = float(scores[best_ai_index])

            if best_score >= threshold:

                matched.append({
                    "source": source_item,
                    "ai": ai_items[best_ai_index],
                    "alignment_score": round(best_score, 4)
                })

                used_ai.add(best_ai_index)

            else:
                missing.append(source_item)

        extra = [
            item
            for index, item in enumerate(ai_items)
            if index not in used_ai
        ]

        return {
            "matched": matched,
            "missing": missing,
            "extra": extra
        }


# Helper function for Block 4
def get_text_items(classified_document):

    return [
        item
        for item in classified_document["content"]
        if item["content_type"] in [
            "text",
            "numeric_fact"
        ]
        and item.get("text")
    ]
'''