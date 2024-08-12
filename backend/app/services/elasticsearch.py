from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError

from sentence_transformers import SentenceTransformer

import logging

logger = logging.getLogger(__name__)


class ElasticsearchService:
    def __init__(self, bi_encoder: str, index_name: str, elastic_password: str):
        # Authenticate
        basic_auth = ("elastic", elastic_password)
        self.es = Elasticsearch("http://elasticsearch:9200", basic_auth=basic_auth)

        # self.bi_encoder = SentenceTransformer(bi_encoder)
        self.index_name = index_name


    def create_index(self, es = None, index_name = None) -> bool:
        """
        Creates an index in Elasticsearch if one does not exist.

        Args:
            es: Elasticsearch instance
            index_name: The name of the index
        """

        if es is None:
            es: Elasticsearch = self.es
        if index_name is None:
            index_name: str = self.index_name

        mappings = {
            "properties": {
                "category": {"type": "keyword", "ignore_above": 256},
                "content": {"type": "text"},
                "date": {"type": "text"},
                "site": {"type": "keyword", "ignore_above": 256},
                "title": {"type": "text"},
                "url": {"type": "keyword", "ignore_above": 256},
                "language": {"type": "keyword", "ignore_above": 256},
                "location": {"type": "keyword", "ignore_above": 256},
                "article_embedding": {
                    "type": "dense_vector", 
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine"
                },
                "tags": {"type": "keyword", "ignore_above": 256}
            }
        }
 
        success = False
        if not es.indices.exists(index=index_name):
            logger.info(f"Creating index {index_name} ...")
            try:
                es.indices.create(
                    index=index_name,
                    settings={"number_of_shards": 1},
                    mappings=mappings
                )
                logger.info(f"{index_name} successfully created")
                success = True
            except RequestError as e:
                if e.error == "resource_already_exists_exception":
                    logger.error(f"{index_name} already exists")
                elif e.error == "invalid_index_name_exception":
                    logger.error(f"Invalid index name {index_name}")
                else:
                    logger.error(f"Error creating index {index_name}")
        else:
            logger.error(f"{index_name} already exists")

        return success

    def search_document(self, query: dict, es = None, index_name = None) -> dict:
        """
        Searches for documents in an index

        Args:
            es: Elasticsearch instance
            indexName: The name of the index
            query: The query to search

        Returns:
            response: The response of the search
        """

        if es is None:
            es: Elasticsearch = self.es
        if index_name is None:
            index_name: str = self.index_name

        try:
            response = es.search(index=index_name, body=query)
            return response
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return {}

    def update_document(self, query: dict, id: id, es = None, index_name = None) -> dict:
        """
        Updates a document in an index based on id
        """

        if es is None:
            es: Elasticsearch = self.es
        if index_name is None:
            index_name: str = self.index_name

        try:
            response = es.update(index=index_name, id=id, body=query)
            return response
        except Exception as e:
            logger.error(f"Error updating index: {e}")
            return {}

    def get_ids(self, response: dict):
        """
        Get the IDs of the documents in the search result
        """
        ids = []
        try:
            if response:
                for hit in response["hits"]["hits"]:
                    ids.append(hit["_id"])
        except Exception as e:
            logger.error(f"Received response is in invalid format")
            return []
        return ids

    def get_field(self, response, field):
        """
        Get a singular field of the documents in search result and returns it as a list
        """
        fields = []
        try:
            if response:
                for hit in response["hits"]["hits"]:
                    fields.append(hit["_source"][field])
        except Exception as e:
            logger.error(f"Received response is in invalid format")
            return []

        return fields

    def get_fields(self, response, fields):
        """
        Get multiple fields from the documents in search results and returns it in JSON format
        """
        results = []

        if len(fields) < 1:
            logger.error("Fields should at least contain 1 or more values")

        try:
            if response:
                for hit in response["hits"]["hits"]:
                    mp = {}
                    for field in fields:
                        mp[field] = hit["_source"][field]
                    results.append(mp)
        except Exception as e:
            logger.error(f"Received response is an invalid format")
            return []

        return results


    def get_all_field(self, query: dict, field: str, es = None, index_name = None):
        """
        Page through the search results to get all the fields in an index
        """

        if es is None:
            es: Elasticsearch = self.es
        if index_name is None:
            index_name: str = self.index_name


        fields_list = []
        res = self.search_document(es, index_name, query)
        ids = self.get_ids(res)

        while res and len(ids) > 0:
            # Update query's search_after
            query["search_after"] = [ids[-1]]
            res = self.search_document(es, index_name, query)
            ids = self.get_ids(res)
            fields = self.get_fields(res, field)
            fields_list.extend(fields)

        return fields_list









