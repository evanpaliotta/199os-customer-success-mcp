"""Zendesk Support Platform Integration - Production Ready"""
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern for API fault tolerance"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds >= self.timeout:
                self.state = "half_open"
                logger.info("circuit_breaker_half_open", message="Attempting recovery")
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("circuit_breaker_closed", message="Service recovered")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    "circuit_breaker_open",
                    failure_count=self.failure_count,
                    message="Circuit breaker opened due to consecutive failures"
                )
            raise e


class ZendeskClient:
    """Production-ready Zendesk API client for support operations"""

    def __init__(self):
        self.subdomain = os.getenv("ZENDESK_SUBDOMAIN")
        self.email = os.getenv("ZENDESK_EMAIL")
        self.token = os.getenv("ZENDESK_API_TOKEN")
        self.client = None
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

        # Check if credentials are configured
        if not all([self.subdomain, self.email, self.token]):
            logger.warning(
                "zendesk_not_configured",
                message="Zendesk credentials not configured - integration will gracefully degrade",
                missing_vars=[
                    var for var, val in {
                        "ZENDESK_SUBDOMAIN": self.subdomain,
                        "ZENDESK_EMAIL": self.email,
                        "ZENDESK_API_TOKEN": self.token
                    }.items() if not val
                ]
            )
            return

        # Initialize Zendesk client
        try:
            from zenpy import Zenpy
            from zenpy.lib.exception import ZenpyException

            self.client = Zenpy(
                subdomain=self.subdomain,
                email=self.email,
                token=self.token
            )
            self.ZenpyException = ZenpyException

            # Test connection
            try:
                self.client.users.me()
                logger.info(
                    "zendesk_client_initialized",
                    subdomain=self.subdomain,
                    email=self.email
                )
            except Exception as e:
                logger.error(
                    "zendesk_connection_test_failed",
                    error=str(e),
                    message="Failed to connect to Zendesk - check credentials"
                )
                self.client = None

        except ImportError:
            logger.warning(
                "zenpy_not_installed",
                message="zenpy library not installed - Zendesk integration unavailable"
            )
            self.client = None

    def _retry_with_backoff(self, func, *args, max_retries: int = 3, **kwargs):
        """Execute function with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check for rate limit (429)
                if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    logger.warning(
                        "zendesk_rate_limit_hit",
                        retry_after=retry_after,
                        attempt=attempt + 1
                    )
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue
                    else:
                        raise Exception(f"Rate limit exceeded. Retry after {retry_after} seconds.")

                # Exponential backoff for other errors
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1  # 1s, 3s, 7s
                    logger.warning(
                        "zendesk_api_error_retrying",
                        error=str(e),
                        attempt=attempt + 1,
                        wait_time=wait_time
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "zendesk_api_error_max_retries",
                        error=str(e),
                        attempts=max_retries
                    )
                    raise e

    def create_ticket(
        self,
        subject: str,
        description: str,
        requester_email: str,
        priority: str = "normal",
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new support ticket in Zendesk.

        Args:
            subject: Ticket subject/title
            description: Ticket description/body
            requester_email: Email of the person requesting support
            priority: Ticket priority (low, normal, high, urgent)
            tags: List of tags to add to the ticket
            custom_fields: Custom field values {field_id: value}

        Returns:
            Dict with status, ticket_id, and ticket_url
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="create_ticket")
            return {
                "status": "degraded",
                "error": "Zendesk not configured - ticket not created",
                "message": "Configure ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN to enable integration"
            }

        try:
            from zenpy.lib.api_objects import Ticket, User, CustomField

            def _create():
                # Create ticket object
                ticket_data = {
                    "subject": subject,
                    "description": description,
                    "priority": priority,
                    "tags": tags or []
                }

                # Add requester
                ticket_data["requester"] = User(email=requester_email)

                # Add custom fields if provided
                if custom_fields:
                    ticket_data["custom_fields"] = [
                        CustomField(id=field_id, value=value)
                        for field_id, value in custom_fields.items()
                    ]

                ticket = Ticket(**ticket_data)

                # Create ticket via API
                created_ticket = self.client.tickets.create(ticket)
                return created_ticket

            # Execute with circuit breaker and retry logic
            created_ticket = self.circuit_breaker.call(
                self._retry_with_backoff,
                _create
            )

            logger.info(
                "zendesk_ticket_created",
                ticket_id=created_ticket.id,
                subject=subject,
                priority=priority,
                requester=requester_email
            )

            return {
                "status": "success",
                "ticket_id": str(created_ticket.id),
                "ticket_url": f"https://{self.subdomain}.zendesk.com/agent/tickets/{created_ticket.id}",
                "created_at": created_ticket.created_at.isoformat() if created_ticket.created_at else None,
                "priority": created_ticket.priority,
                "status_zendesk": created_ticket.status
            }

        except Exception as e:
            logger.error(
                "zendesk_ticket_creation_failed",
                error=str(e),
                subject=subject,
                requester=requester_email
            )
            return {
                "status": "failed",
                "error": str(e),
                "message": "Failed to create Zendesk ticket"
            }

    def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """
        Retrieve a ticket by ID.

        Args:
            ticket_id: Zendesk ticket ID

        Returns:
            Dict with ticket details
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="get_ticket")
            return {
                "status": "degraded",
                "error": "Zendesk not configured"
            }

        try:
            def _get():
                return self.client.tickets(id=ticket_id)

            ticket = self.circuit_breaker.call(
                self._retry_with_backoff,
                _get
            )

            logger.info("zendesk_ticket_retrieved", ticket_id=ticket_id)

            return {
                "status": "success",
                "ticket_id": str(ticket.id),
                "subject": ticket.subject,
                "description": ticket.description,
                "status_zendesk": ticket.status,
                "priority": ticket.priority,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
                "requester_id": ticket.requester_id,
                "assignee_id": ticket.assignee_id,
                "tags": ticket.tags or [],
                "ticket_url": f"https://{self.subdomain}.zendesk.com/agent/tickets/{ticket.id}"
            }

        except Exception as e:
            logger.error(
                "zendesk_get_ticket_failed",
                error=str(e),
                ticket_id=ticket_id
            )
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Failed to retrieve ticket {ticket_id}"
            }

    def update_ticket(
        self,
        ticket_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        subject: Optional[str] = None,
        comment: Optional[str] = None,
        public_comment: bool = True
    ) -> Dict[str, Any]:
        """
        Update an existing ticket.

        Args:
            ticket_id: Zendesk ticket ID
            status: New status (new, open, pending, hold, solved, closed)
            priority: New priority (low, normal, high, urgent)
            assignee_id: Zendesk user ID to assign ticket to
            tags: New tags to add to ticket
            custom_fields: Custom field updates {field_id: value}
            subject: Updated ticket subject
            comment: Comment to add with update
            public_comment: Whether comment is visible to requester

        Returns:
            Dict with update status
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="update_ticket")
            return {
                "status": "degraded",
                "error": "Zendesk not configured"
            }

        try:
            from zenpy.lib.api_objects import Ticket, CustomField, Comment

            def _update():
                # Get existing ticket
                ticket = self.client.tickets(id=ticket_id)

                # Update fields
                if status:
                    ticket.status = status
                if priority:
                    ticket.priority = priority
                if assignee_id:
                    ticket.assignee_id = assignee_id
                if subject:
                    ticket.subject = subject
                if tags:
                    # Merge with existing tags
                    existing_tags = set(ticket.tags or [])
                    existing_tags.update(tags)
                    ticket.tags = list(existing_tags)
                if custom_fields:
                    ticket.custom_fields = [
                        CustomField(id=field_id, value=value)
                        for field_id, value in custom_fields.items()
                    ]

                # Add comment if provided
                if comment:
                    ticket.comment = Comment(
                        body=comment,
                        public=public_comment
                    )

                # Update ticket via API
                updated_ticket = self.client.tickets.update(ticket)
                return updated_ticket

            updated_ticket = self.circuit_breaker.call(
                self._retry_with_backoff,
                _update
            )

            logger.info(
                "zendesk_ticket_updated",
                ticket_id=ticket_id,
                status=status,
                priority=priority,
                comment_added=bool(comment)
            )

            return {
                "status": "success",
                "ticket_id": str(updated_ticket.id),
                "updated_at": updated_ticket.updated_at.isoformat() if updated_ticket.updated_at else None,
                "status_zendesk": updated_ticket.status,
                "priority": updated_ticket.priority,
                "comment_added": bool(comment),
                "ticket_url": f"https://{self.subdomain}.zendesk.com/agent/tickets/{updated_ticket.id}"
            }

        except Exception as e:
            logger.error(
                "zendesk_update_ticket_failed",
                error=str(e),
                ticket_id=ticket_id
            )
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Failed to update ticket {ticket_id}"
            }

    def add_comment(
        self,
        ticket_id: str,
        comment_body: str,
        public: bool = True,
        author_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add a comment to a ticket.

        Args:
            ticket_id: Zendesk ticket ID
            comment_body: Comment text
            public: Whether comment is public (visible to requester)
            author_id: Zendesk user ID of comment author

        Returns:
            Dict with comment status
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="add_comment")
            return {
                "status": "degraded",
                "error": "Zendesk not configured"
            }

        try:
            from zenpy.lib.api_objects import Ticket, Comment

            def _add_comment():
                # Get existing ticket
                ticket = self.client.tickets(id=ticket_id)

                # Create comment
                comment = Comment(
                    body=comment_body,
                    public=public
                )
                if author_id:
                    comment.author_id = author_id

                ticket.comment = comment

                # Update ticket with comment
                updated_ticket = self.client.tickets.update(ticket)
                return updated_ticket

            updated_ticket = self.circuit_breaker.call(
                self._retry_with_backoff,
                _add_comment
            )

            logger.info(
                "zendesk_comment_added",
                ticket_id=ticket_id,
                public=public
            )

            return {
                "status": "success",
                "ticket_id": str(updated_ticket.id),
                "comment_added": True,
                "public": public,
                "ticket_url": f"https://{self.subdomain}.zendesk.com/agent/tickets/{updated_ticket.id}"
            }

        except Exception as e:
            logger.error(
                "zendesk_add_comment_failed",
                error=str(e),
                ticket_id=ticket_id
            )
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Failed to add comment to ticket {ticket_id}"
            }

    def get_user(self, email: str) -> Dict[str, Any]:
        """
        Get Zendesk user by email.

        Args:
            email: User email address

        Returns:
            Dict with user details
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="get_user")
            return {
                "status": "degraded",
                "error": "Zendesk not configured"
            }

        try:
            def _search():
                # Search for user by email
                users = self.client.search(email, type='user')
                return list(users)

            users = self.circuit_breaker.call(
                self._retry_with_backoff,
                _search
            )

            if not users:
                return {
                    "status": "not_found",
                    "message": f"No user found with email {email}"
                }

            user = users[0]

            logger.info("zendesk_user_retrieved", email=email, user_id=user.id)

            return {
                "status": "success",
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "organization_id": user.organization_id,
                "tags": user.tags or []
            }

        except Exception as e:
            logger.error(
                "zendesk_get_user_failed",
                error=str(e),
                email=email
            )
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Failed to retrieve user {email}"
            }

    def search_tickets(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        requester_email: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search tickets by various criteria.

        Args:
            query: Free-text search query
            status: Filter by status (new, open, pending, hold, solved, closed)
            priority: Filter by priority (low, normal, high, urgent)
            requester_email: Filter by requester email
            tags: Filter by tags (must have all tags)
            limit: Maximum number of results

        Returns:
            Dict with search results
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="search_tickets")
            return {
                "status": "degraded",
                "error": "Zendesk not configured",
                "tickets": []
            }

        try:
            # Build search query
            search_terms = []

            if query:
                search_terms.append(query)
            if status:
                search_terms.append(f"status:{status}")
            if priority:
                search_terms.append(f"priority:{priority}")
            if requester_email:
                search_terms.append(f"requester:{requester_email}")
            if tags:
                for tag in tags:
                    search_terms.append(f"tags:{tag}")

            search_query = " ".join(search_terms) if search_terms else "*"

            def _search():
                # Search tickets
                results = self.client.search(search_query, type='ticket')
                tickets = []
                for i, ticket in enumerate(results):
                    if i >= limit:
                        break
                    tickets.append(ticket)
                return tickets

            tickets = self.circuit_breaker.call(
                self._retry_with_backoff,
                _search
            )

            logger.info(
                "zendesk_tickets_searched",
                query=search_query,
                results_count=len(tickets)
            )

            # Format results
            formatted_tickets = []
            for ticket in tickets:
                formatted_tickets.append({
                    "ticket_id": str(ticket.id),
                    "subject": ticket.subject,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                    "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
                    "requester_id": ticket.requester_id,
                    "assignee_id": ticket.assignee_id,
                    "tags": ticket.tags or [],
                    "ticket_url": f"https://{self.subdomain}.zendesk.com/agent/tickets/{ticket.id}"
                })

            return {
                "status": "success",
                "query": search_query,
                "results_count": len(formatted_tickets),
                "tickets": formatted_tickets
            }

        except Exception as e:
            logger.error(
                "zendesk_search_tickets_failed",
                error=str(e),
                query=query
            )
            return {
                "status": "failed",
                "error": str(e),
                "message": "Failed to search tickets",
                "tickets": []
            }

    def create_user(
        self,
        name: str,
        email: str,
        role: str = "end-user",
        organization_id: Optional[int] = None,
        phone: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Zendesk user.

        Args:
            name: User's full name
            email: User's email address
            role: User role (end-user, agent, admin)
            organization_id: Organization ID to associate user with
            phone: User's phone number
            tags: Tags for user
            user_fields: Custom user field values

        Returns:
            Dict with user creation status
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="create_user")
            return {
                "status": "degraded",
                "error": "Zendesk not configured"
            }

        try:
            from zenpy.lib.api_objects import User

            def _create():
                user_data = {
                    "name": name,
                    "email": email,
                    "role": role
                }

                if organization_id:
                    user_data["organization_id"] = organization_id
                if phone:
                    user_data["phone"] = phone
                if tags:
                    user_data["tags"] = tags
                if user_fields:
                    user_data["user_fields"] = user_fields

                user = User(**user_data)
                created_user = self.client.users.create(user)
                return created_user

            created_user = self.circuit_breaker.call(
                self._retry_with_backoff,
                _create
            )

            logger.info(
                "zendesk_user_created",
                user_id=created_user.id,
                email=email,
                role=role
            )

            return {
                "status": "success",
                "user_id": created_user.id,
                "name": created_user.name,
                "email": created_user.email,
                "role": created_user.role,
                "created_at": created_user.created_at.isoformat() if created_user.created_at else None
            }

        except Exception as e:
            logger.error(
                "zendesk_create_user_failed",
                error=str(e),
                email=email
            )
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Failed to create user {email}"
            }

    def bulk_create_tickets(
        self,
        tickets: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Create multiple tickets in bulk.

        Args:
            tickets: List of ticket dictionaries with subject, description, requester_email
            batch_size: Number of tickets per API call (max 100)

        Returns:
            Dict with bulk creation results
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="bulk_create_tickets")
            return {
                "status": "degraded",
                "error": "Zendesk not configured",
                "total": 0,
                "successful": 0,
                "failed": 0
            }

        try:
            from zenpy.lib.api_objects import Ticket, User

            total = len(tickets)
            successful = 0
            failed = 0
            errors = []
            created_ticket_ids = []

            # Process in batches
            for i in range(0, total, batch_size):
                batch = tickets[i:i + batch_size]

                def _create_batch():
                    ticket_objects = []
                    for ticket_data in batch:
                        ticket = Ticket(
                            subject=ticket_data.get('subject'),
                            description=ticket_data.get('description'),
                            requester=User(email=ticket_data.get('requester_email')),
                            priority=ticket_data.get('priority', 'normal'),
                            tags=ticket_data.get('tags', [])
                        )
                        ticket_objects.append(ticket)

                    # Zenpy bulk create
                    job_status = self.client.tickets.create_many(ticket_objects)
                    return job_status

                try:
                    job = self.circuit_breaker.call(
                        self._retry_with_backoff,
                        _create_batch
                    )

                    # Track success
                    successful += len(batch)
                    logger.info(
                        "zendesk_bulk_tickets_created",
                        batch_size=len(batch),
                        batch_num=i // batch_size + 1
                    )

                except Exception as e:
                    failed += len(batch)
                    errors.append({
                        'batch': i // batch_size + 1,
                        'error': str(e)
                    })
                    logger.error(
                        "zendesk_bulk_create_batch_failed",
                        batch_num=i // batch_size + 1,
                        error=str(e)
                    )

            return {
                "status": "success" if failed == 0 else "partial",
                "total": total,
                "successful": successful,
                "failed": failed,
                "errors": errors if errors else None,
                "message": f"Created {successful}/{total} tickets successfully"
            }

        except Exception as e:
            logger.error(
                "zendesk_bulk_create_failed",
                error=str(e),
                total_tickets=len(tickets)
            )
            return {
                "status": "failed",
                "error": str(e),
                "total": len(tickets),
                "successful": 0,
                "failed": len(tickets)
            }

    def bulk_update_tickets(
        self,
        ticket_updates: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Update multiple tickets in bulk.

        Args:
            ticket_updates: List of dicts with ticket_id and update fields
            batch_size: Number of tickets per API call

        Returns:
            Dict with bulk update results
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="bulk_update_tickets")
            return {
                "status": "degraded",
                "error": "Zendesk not configured",
                "total": 0,
                "successful": 0,
                "failed": 0
            }

        try:
            from zenpy.lib.api_objects import Ticket

            total = len(ticket_updates)
            successful = 0
            failed = 0
            errors = []

            # Process in batches
            for i in range(0, total, batch_size):
                batch = ticket_updates[i:i + batch_size]

                def _update_batch():
                    tickets_to_update = []
                    for update_data in batch:
                        ticket_id = update_data.get('ticket_id')
                        ticket = self.client.tickets(id=ticket_id)

                        # Apply updates
                        if 'status' in update_data:
                            ticket.status = update_data['status']
                        if 'priority' in update_data:
                            ticket.priority = update_data['priority']
                        if 'tags' in update_data:
                            existing_tags = set(ticket.tags or [])
                            existing_tags.update(update_data['tags'])
                            ticket.tags = list(existing_tags)

                        tickets_to_update.append(ticket)

                    # Bulk update
                    job_status = self.client.tickets.update_many(tickets_to_update)
                    return job_status

                try:
                    job = self.circuit_breaker.call(
                        self._retry_with_backoff,
                        _update_batch
                    )

                    successful += len(batch)
                    logger.info(
                        "zendesk_bulk_tickets_updated",
                        batch_size=len(batch),
                        batch_num=i // batch_size + 1
                    )

                except Exception as e:
                    failed += len(batch)
                    errors.append({
                        'batch': i // batch_size + 1,
                        'error': str(e)
                    })
                    logger.error(
                        "zendesk_bulk_update_batch_failed",
                        batch_num=i // batch_size + 1,
                        error=str(e)
                    )

            return {
                "status": "success" if failed == 0 else "partial",
                "total": total,
                "successful": successful,
                "failed": failed,
                "errors": errors if errors else None,
                "message": f"Updated {successful}/{total} tickets successfully"
            }

        except Exception as e:
            logger.error(
                "zendesk_bulk_update_failed",
                error=str(e),
                total_tickets=len(ticket_updates)
            )
            return {
                "status": "failed",
                "error": str(e),
                "total": len(ticket_updates),
                "successful": 0,
                "failed": len(ticket_updates)
            }

    def get_ticket_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ticket metrics and statistics.

        Args:
            start_date: Start date for metrics (YYYY-MM-DD)
            end_date: End date for metrics (YYYY-MM-DD)

        Returns:
            Dict with ticket metrics
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="get_ticket_metrics")
            return {
                "status": "degraded",
                "error": "Zendesk not configured"
            }

        try:
            def _get_metrics():
                # Use Zendesk incremental API for efficiency
                metrics = {
                    "total_tickets": 0,
                    "open_tickets": 0,
                    "pending_tickets": 0,
                    "solved_tickets": 0,
                    "by_priority": {"low": 0, "normal": 0, "high": 0, "urgent": 0}
                }

                # Query tickets
                for ticket in self.client.tickets():
                    metrics["total_tickets"] += 1

                    if ticket.status == "open":
                        metrics["open_tickets"] += 1
                    elif ticket.status == "pending":
                        metrics["pending_tickets"] += 1
                    elif ticket.status == "solved":
                        metrics["solved_tickets"] += 1

                    priority = ticket.priority or "normal"
                    if priority in metrics["by_priority"]:
                        metrics["by_priority"][priority] += 1

                return metrics

            metrics = self.circuit_breaker.call(
                self._retry_with_backoff,
                _get_metrics
            )

            logger.info("zendesk_metrics_retrieved", total_tickets=metrics["total_tickets"])

            return {
                "status": "success",
                "metrics": metrics,
                "period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }

        except Exception as e:
            logger.error("zendesk_get_metrics_failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "message": "Failed to retrieve ticket metrics"
            }

    def get_sla_policy(self, policy_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get SLA policy information.

        Args:
            policy_id: Specific SLA policy ID (optional)

        Returns:
            Dict with SLA policy details
        """
        if not self.client:
            logger.warning("zendesk_not_configured", action="get_sla_policy")
            return {
                "status": "degraded",
                "error": "Zendesk not configured"
            }

        try:
            def _get_policy():
                if policy_id:
                    return self.client.sla_policies(id=policy_id)
                else:
                    # Get all policies
                    return list(self.client.sla_policies())

            policies = self.circuit_breaker.call(
                self._retry_with_backoff,
                _get_policy
            )

            logger.info("zendesk_sla_policy_retrieved")

            if isinstance(policies, list):
                return {
                    "status": "success",
                    "policies": [
                        {
                            "id": p.id,
                            "title": p.title,
                            "description": p.description
                        }
                        for p in policies
                    ]
                }
            else:
                return {
                    "status": "success",
                    "policy": {
                        "id": policies.id,
                        "title": policies.title,
                        "description": policies.description
                    }
                }

        except Exception as e:
            logger.error("zendesk_get_sla_policy_failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "message": "Failed to retrieve SLA policy"
            }

    def close(self):
        """Close the Zendesk client and cleanup resources"""
        if self.client:
            logger.info("zendesk_client_closing")
            self.client = None
        logger.info("zendesk_client_closed")
