"""
manage_knowledge_base - Process 110: Knowledge base management for self-service support

Process 110: Knowledge base management for self-service support.

Manages the complete knowledge base lifecycle including article creation,
search, categorization, and analytics. Enables customers to find solutions
independently and reduces ticket volume.

Actions:
- search: Search knowledge base articles
- create: Create new article
- get: Get specific article by ID
- list: List articles by category
- recommend: Get article recommendations
- analytics: Get KB usage analytics

Args:
    action: Action to perform (search, create, get, list, recommend, analytics)
    article_id: Article identifier (required for get)
    title: Article title (required for create)
    summary: Brief article summary (required for create)
    content: Full article content in markdown (required for create)
    category: Primary category
    subcategory: Subcategory for organization
    tags: Tags for search and categorization
    search_query: Search query string
    search_category: Filter search by category
    status: Article status (draft, review, published, archived)
    author: Article author name
    limit: Maximum number of results to return
    include_drafts: Whether to include draft articles

Returns:
    Knowledge base operation results with articles, search results, or analytics
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
import structlog
from src.models.support_models import (

    async def manage_knowledge_base(
        ctx: Context,
        action: str = "search",
        article_id: Optional[str] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        search_category: Optional[str] = None,
        status: str = "published",
        author: Optional[str] = None,
        limit: int = 10,
        include_drafts: bool = False
    ) -> Dict[str, Any]:
        """
        Process 110: Knowledge base management for self-service support.

        Manages the complete knowledge base lifecycle including article creation,
        search, categorization, and analytics. Enables customers to find solutions
        independently and reduces ticket volume.

        Actions:
        - search: Search knowledge base articles
        - create: Create new article
        - get: Get specific article by ID
        - list: List articles by category
        - recommend: Get article recommendations
        - analytics: Get KB usage analytics

        Args:
            action: Action to perform (search, create, get, list, recommend, analytics)
            article_id: Article identifier (required for get)
            title: Article title (required for create)
            summary: Brief article summary (required for create)
            content: Full article content in markdown (required for create)
            category: Primary category
            subcategory: Subcategory for organization
            tags: Tags for search and categorization
            search_query: Search query string
            search_category: Filter search by category
            status: Article status (draft, review, published, archived)
            author: Article author name
            limit: Maximum number of results to return
            include_drafts: Whether to include draft articles

        Returns:
            Knowledge base operation results with articles, search results, or analytics
        """
        try:
            await ctx.info(f"Managing knowledge base: {action}")

            # Validate action
            valid_actions = ['search', 'create', 'get', 'list', 'recommend', 'analytics']
            if action not in valid_actions:
                return {
                    'status': 'failed',
                    'error': f"Invalid action. Must be one of: {', '.join(valid_actions)}"
                }

            # SEARCH KNOWLEDGE BASE
            if action == "search":
                if not search_query:
                    return {
                        'status': 'failed',
                        'error': 'search_query is required for search action'
                    }

                # Sanitize search query
                search_query = SecurityValidator.validate_no_sql_injection(search_query)

                # Search articles (mock implementation)
                results = _search_knowledge_base(
                    query=search_query,
                    category=search_category,
                    status=status,
                    include_drafts=include_drafts,
                    limit=limit
                )

                logger.info(
                    "kb_search_performed",
                    query=search_query,
                    results_found=len(results)
                )

                return {
                    'status': 'success',
                    'search_query': search_query,
                    'results_found': len(results),
                    'articles': results,
                    'search_suggestions': _generate_search_suggestions(search_query),
                    'related_categories': _get_related_categories(results)
                }

            # CREATE ARTICLE
            elif action == "create":
                if not all([title, summary, content, category, tags, author]):
                    return {
                        'status': 'failed',
                        'error': 'Missing required fields: title, summary, content, category, tags, author'
                    }

                # Sanitize inputs
                title = SecurityValidator.validate_no_xss(title)
                summary = SecurityValidator.validate_no_xss(summary)
                content = SecurityValidator.validate_no_xss(content)

                # Generate article ID
                timestamp = int(datetime.now().timestamp())
                new_article_id = f"KB-{timestamp % 10000}"

                # Create article
                try:
                    article = KnowledgeBaseArticle(
                        article_id=new_article_id,
                        title=title,
                        summary=summary,
                        content=content,
                        category=category,
                        subcategory=subcategory,
                        tags=tags,
                        status=ArticleStatus.DRAFT,  # Start as draft
                        author=author,
                        search_keywords=_extract_keywords(title, content, tags)
                    )

                    logger.info(
                        "kb_article_created",
                        article_id=new_article_id,
                        title=title,
                        category=category
                    )

                    return {
                        'status': 'success',
                        'message': f"Article {new_article_id} created successfully",
                        'article_id': new_article_id,
                        'article': article.model_dump(),
                        'next_steps': [
                            "Article created in DRAFT status",
                            "Review and edit content as needed",
                            "Submit for review when ready",
                            "Publish to make available to customers"
                        ]
                    }

                except Exception as e:
                    return {
                        'status': 'failed',
                        'error': f"Failed to create article: {str(e)}"
                    }

            # GET ARTICLE
            elif action == "get":
                if not article_id:
                    return {
                        'status': 'failed',
                        'error': 'article_id is required for get action'
                    }

                # Get article (mock data)
                article_data = _get_mock_article(article_id)
                if not article_data:
                    return {
                        'status': 'failed',
                        'error': f'Article not found: {article_id}'
                    }

                article = KnowledgeBaseArticle(**article_data)

                # Increment view count
                article.view_count += 1

                # Get related articles
                related = _get_related_articles(article)

                logger.info("kb_article_viewed", article_id=article_id)

                return {
                    'status': 'success',
                    'article': article.model_dump(),
                    'related_articles': related,
                    'metrics': {
                        'view_count': article.view_count,
                        'helpfulness_score': article.helpfulness_score,
                        'total_votes': article.helpful_votes + article.not_helpful_votes
                    }
                }

            # LIST ARTICLES
            elif action == "list":
                # Get articles by category (mock data)
                articles = _list_articles_by_category(
                    category=category,
                    subcategory=subcategory,
                    status=status,
                    include_drafts=include_drafts,
                    limit=limit
                )

                # Group by subcategory
                grouped = defaultdict(list)
                for article in articles:
                    subcat = article.get('subcategory', 'Uncategorized')
                    grouped[subcat].append(article)

                return {
                    'status': 'success',
                    'category': category,
                    'total_articles': len(articles),
                    'articles_by_subcategory': dict(grouped),
                    'articles': articles
                }

            # RECOMMEND ARTICLES
            elif action == "recommend":
                # Get recommendations based on popular articles and user behavior
                recommendations = _get_article_recommendations(
                    category=category,
                    limit=limit
                )

                return {
                    'status': 'success',
                    'recommended_articles': recommendations,
                    'recommendation_basis': [
                        'High helpfulness scores',
                        'Frequently viewed',
                        'Recently updated',
                        'Related to common issues'
                    ]
                }

            # KB ANALYTICS
            elif action == "analytics":
                analytics = _get_kb_analytics(
                    category=category,
                    days=30
                )

                return {
                    'status': 'success',
                    'analytics': analytics,
                    'insights': _generate_kb_insights(analytics)
                }

        except Exception as e:
            logger.error(
                "manage_knowledge_base_failed",
                action=action,
                error=str(e)
            )
            return {
                'status': 'failed',
                'error': f"Failed to manage knowledge base: {str(e)}"
            }
