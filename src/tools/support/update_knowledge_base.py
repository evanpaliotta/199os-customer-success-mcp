"""
update_knowledge_base - Process 111: Knowledge base updates and maintenance

Process 111: Knowledge base updates and maintenance.

Updates existing KB articles including content, metadata, status,
and versioning. Tracks article effectiveness through voting and
manages publication lifecycle.

Actions:
- update: Update article content/metadata
- publish: Publish draft article
- archive: Archive outdated article
- vote: Record helpfulness vote
- increment_version: Create new version

Args:
    article_id: Article identifier (required)
    action: Update action (update, publish, archive, vote, increment_version)
    title: Updated article title
    summary: Updated summary
    content: Updated content
    category: Updated category
    subcategory: Updated subcategory
    tags: Updated tags
    status: Updated status (draft, review, published, archived)
    helpful_vote: True for helpful, False for not helpful
    publish: Publish the article immediately
    archive: Archive the article

Returns:
    Update confirmation with article details, version info, and impact metrics
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
import structlog
from src.models.support_models import (
from src.decorators import mcp_tool
from src.composio import get_composio_client
async def update_knowledge_base(
        ctx: Context,
        article_id: str,
        action: str = "update",
        title: Optional[str] = None,
        summary: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        helpful_vote: Optional[bool] = None,
        publish: bool = False,
        archive: bool = False
    ) -> Dict[str, Any]:
        """
        Process 111: Knowledge base updates and maintenance.

        Updates existing KB articles including content, metadata, status,
        and versioning. Tracks article effectiveness through voting and
        manages publication lifecycle.

        Actions:
        - update: Update article content/metadata
        - publish: Publish draft article
        - archive: Archive outdated article
        - vote: Record helpfulness vote
        - increment_version: Create new version

        Args:
            article_id: Article identifier (required)
            action: Update action (update, publish, archive, vote, increment_version)
            title: Updated article title
            summary: Updated summary
            content: Updated content
            category: Updated category
            subcategory: Updated subcategory
            tags: Updated tags
            status: Updated status (draft, review, published, archived)
            helpful_vote: True for helpful, False for not helpful
            publish: Publish the article immediately
            archive: Archive the article

        Returns:
            Update confirmation with article details, version info, and impact metrics
        """
        try:
            await ctx.info(f"Updating KB article: {article_id}")

            # Get existing article
            article_data = _get_mock_article(article_id)
            if not article_data:
                return {
                    'status': 'failed',
                    'error': f'Article not found: {article_id}'
                }

            article = KnowledgeBaseArticle(**article_data)
            changes = []

            # UPDATE CONTENT/METADATA
            if action == "update":
                if title:
                    old_title = article.title
                    article.title = SecurityValidator.validate_no_xss(title)
                    changes.append(f"title: '{old_title}' -> '{article.title}'")

                if summary:
                    article.summary = SecurityValidator.validate_no_xss(summary)
                    changes.append("summary updated")

                if content:
                    article.content = SecurityValidator.validate_no_xss(content)
                    article.version += 1  # Increment version on content change
                    changes.append(f"content updated (version {article.version})")

                if category:
                    article.category = category
                    changes.append(f"category -> {category}")

                if subcategory:
                    article.subcategory = subcategory
                    changes.append(f"subcategory -> {subcategory}")

                if tags:
                    article.tags = tags
                    article.search_keywords = _extract_keywords(article.title, article.content, tags)
                    changes.append(f"tags updated: {tags}")

                if status:
                    article.status = ArticleStatus(status)
                    changes.append(f"status -> {status}")

                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_updated",
                    article_id=article_id,
                    changes=changes
                )

                return {
                    'status': 'success',
                    'message': f"Article {article_id} updated successfully",
                    'article_id': article_id,
                    'changes': changes,
                    'article': article.model_dump(),
                    'version': article.version
                }

            # PUBLISH ARTICLE
            elif action == "publish" or publish:
                if article.status == ArticleStatus.PUBLISHED:
                    return {
                        'status': 'failed',
                        'error': 'Article is already published'
                    }

                article.status = ArticleStatus.PUBLISHED
                article.published_at = datetime.now()
                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_published",
                    article_id=article_id,
                    title=article.title
                )

                return {
                    'status': 'success',
                    'message': f"Article {article_id} published successfully",
                    'article_id': article_id,
                    'article': article.model_dump(),
                    'publication': {
                        'published_at': article.published_at.isoformat(),
                        'version': article.version,
                        'category': article.category
                    },
                    'distribution': [
                        "Article now visible in customer portal",
                        "Indexed for search",
                        "Added to category listing",
                        "Included in recommendations"
                    ]
                }

            # ARCHIVE ARTICLE
            elif action == "archive" or archive:
                if article.status == ArticleStatus.ARCHIVED:
                    return {
                        'status': 'failed',
                        'error': 'Article is already archived'
                    }

                old_status = article.status
                article.status = ArticleStatus.ARCHIVED
                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_archived",
                    article_id=article_id,
                    title=article.title
                )

                return {
                    'status': 'success',
                    'message': f"Article {article_id} archived successfully",
                    'article_id': article_id,
                    'article': article.model_dump(),
                    'archival': {
                        'archived_at': article.updated_at.isoformat(),
                        'previous_status': old_status.value,
                        'total_views': article.view_count,
                        'helpfulness_score': article.helpfulness_score
                    },
                    'impact': [
                        "Article removed from public listings",
                        "No longer appears in search results",
                        "Historic analytics preserved",
                        "Can be restored if needed"
                    ]
                }

            # RECORD VOTE
            elif action == "vote":
                if helpful_vote is None:
                    return {
                        'status': 'failed',
                        'error': 'helpful_vote (True/False) is required for vote action'
                    }

                if helpful_vote:
                    article.helpful_votes += 1
                else:
                    article.not_helpful_votes += 1

                article.calculate_helpfulness_score()
                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_vote_recorded",
                    article_id=article_id,
                    helpful=helpful_vote,
                    new_score=article.helpfulness_score
                )

                return {
                    'status': 'success',
                    'message': f"Vote recorded for article {article_id}",
                    'article_id': article_id,
                    'vote': 'helpful' if helpful_vote else 'not helpful',
                    'metrics': {
                        'helpful_votes': article.helpful_votes,
                        'not_helpful_votes': article.not_helpful_votes,
                        'total_votes': article.helpful_votes + article.not_helpful_votes,
                        'helpfulness_score': article.helpfulness_score
                    },
                    'article': article.model_dump()
                }

            # INCREMENT VERSION
            elif action == "increment_version":
                article.version += 1
                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_version_incremented",
                    article_id=article_id,
                    new_version=article.version
                )

                return {
                    'status': 'success',
                    'message': f"Article {article_id} version incremented",
                    'article_id': article_id,
                    'version': article.version,
                    'article': article.model_dump()
                }

            else:
                return {
                    'status': 'failed',
                    'error': f"Invalid action: {action}"
                }

        except Exception as e:
            logger.error(
                "update_knowledge_base_failed",
                article_id=article_id,
                action=action,
                error=str(e)
            )
            return {
                'status': 'failed',
                'error': f"Failed to update knowledge base: {str(e)}"
            }
