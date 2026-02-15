# Agent Memory & Agenda MCP Server - Usage Guidelines

## Purpose
This MCP server provides two core engines for AI assistants:
1. **Memory Engine**: Long-term persistent memory storage for project context, decisions, and preferences.
2. **Agenda Engine**: Task management system to create, track, and manage multi-step plans and todo lists.

---

## Part 1: Memory Engine

(Sections for Memory Engine follow...)

## When to Save Memories

### ✅ DO Save:
- **Architecture decisions**: Technical choices, library selections, design patterns, code style, project constraints, decisions on picking approaches/tools with reasoning
- **Project context**: Key files, important functions, system behavior, development status summaries, insights gained during problem-solving
- **Feature development**: New features specifications and requirements
- **Bug fixes**: Root causes and solutions for issues encountered
- **Important facts**: Information collected from user or other sources

### ❌ DON'T Save:
- Temporary conversation details
- Publicly available information (use web search instead)
- Sensitive data like passwords or API keys
- Obvious facts that can be inferred from code
- Redundant information already in the codebase

## How to Structure Memories

### Category
Choose descriptive categories that help with search and organization:
- `architecture` - System design, tech stack, patterns, constraints
- `bug_fix` - Bug descriptions and solutions
- `feature` - Feature specifications and requirements
- `context` - Project-specific context, insights and summaries of important development checkpoints
- `keepsake` - Gathered information from user or other sources

**Tip**: Categories are searchable! Users can search by category name.

### Topic
A short, descriptive title (3-10 words):
- ✅ Good: "Database choice for user data"
- ✅ Good: "Authentication flow implementation"
- ❌ Bad: "Decision" (too vague)
- ❌ Bad: "We decided to use PostgreSQL because it has JSONB support and is reliable" (too long, belongs in content)

### Content
Detailed information with context:
- Include the "why" behind decisions
- Add relevant context (when, what problem it solves)
- Be specific and actionable
- Include key technical details

**Example:**
```
Category: architecture
Topic: Database choice for user data
Content: Chose PostgreSQL over MongoDB for the user management system because:
1. We need ACID guarantees for user transactions
2. JSONB support handles flexible user metadata
3. Team has more PostgreSQL experience
4. Heroku deployment is simpler with Postgres
Decision made: 2024-02-04
```

## How to Query Memories

### Query Strategies

1. **Natural language**: "What database are we using?"
2. **Category search**: "architecture decisions" or "bug_fix authentication"
3. **Keyword search**: "PostgreSQL" or "user preferences"
4. **Semantic search**: The system understands related concepts

### Query Examples

```python
# Find architecture decisions
query_memory("architecture database", top_k=3)

# Find user preferences
query_memory("code style preferences", top_k=5)

# Find bug fixes related to auth
query_memory("authentication bug", top_k=3)

# Find any memory about PostgreSQL
query_memory("PostgreSQL", top_k=5)
```

### Understanding Results

Results include:
- `id`: Unique identifier for updates/deletes
- `category`: Memory category
- `topic`: Short title
- `content`: Full details
- `timestamp`: When the memory was originally saved
- `score`: Relevance score (higher = better match)

Results are ranked by relevance using hybrid search (keyword + semantic).

## Best Practices

### 1. Query Before Saving
Always query first to avoid duplicates:
```python
# Check if memory exists
results = query_memory("database choice")
if not results:
    save_memory(
        category="architecture",
        topic="Database choice",
        content="Chose PostgreSQL..."
    )
```

### 2. Update Instead of Duplicate
If a memory needs modification, update it:
```python
# Update existing memory
update_memory(
    doc_id=123,
    content="Updated: Chose PostgreSQL v15 specifically..."
)
```

### 3. Be Proactive but Selective
- Save important decisions as they're made
- Don't wait until end of conversation
- But don't save every small detail

### 4. Use Consistent Categories
Stick to established category names for better organization:
- Check existing memories to see what categories are used
- Reuse categories when possible

### 5. Make Content Searchable
Include keywords and terms users might search for:
- ✅ "We chose React (not Vue or Angular) for the frontend..."
- ❌ "We chose it for the UI..."

### 6. Delete Outdated Memories
Clean up superseded or incorrect information:
```python
# Delete old memory
delete_memory(doc_id=123)

# Then save the new version
save_memory(...)
```

## Common Patterns

### Pattern 1: Save Architecture Decision
```python
save_memory(
    category="architecture",
    topic="API framework selection",
    content="Chose FastAPI over Flask because: async support, automatic OpenAPI docs, type hints, and modern Python features. Team agreed on 2024-02-04."
)
```

### Pattern 2: Save User Preference
```python
save_memory(
    category="preference",
    topic="Import ordering style",
    content="User prefers imports ordered as: stdlib, third-party, local. Use isort with profile=black. Established during PR review."
)
```

### Pattern 3: Save Bug Fix Context
```python
save_memory(
    category="bug_fix",
    topic="Memory leak in WebSocket handler",
    content="Root cause: WebSocket connections weren't properly closed on error. Solution: Added explicit close() in finally block. Affects files: server.py, websocket_handler.py. Fixed: 2024-02-04."
)
```

### Pattern 4: Query and Update
```python
# Find existing memory
results = query_memory("database choice")
if results:
    memory = results[0]
    # Update with new information
    update_memory(
        doc_id=memory['id'],
        content=memory['content'] + "\n\nUpdate 2024-02-05: Upgraded to PostgreSQL 15 for better JSON performance."
    )
```

## Search Features

### Hybrid Search
The system uses both:
- **Keyword search (FTS5)**: Exact and fuzzy text matching across category, topic, and content
- **Semantic search (Vector)**: Understands meaning and related concepts
- **Reciprocal Rank Fusion**: Combines both for best results

### What's Searchable
All three fields are indexed for search:
- ✅ `category` - Search by category name
- ✅ `topic` - Search by title keywords
- ✅ `content` - Search by detailed content

### Search Performance
- First query: ~500ms (model warm-up)
- Subsequent queries: <200ms
- Top-k results ranked by relevance

## Error Handling

### Check Results
```python
results = query_memory("something")
if not results:
    # No memories found, might need to save one
    pass
```

### Verify Operations
```python
result = save_memory(...)
if result['status'] == 'success':
    doc_id = result['doc_id']
    # Use doc_id for future updates
```

### Handle Missing Memories
```python
result = update_memory(doc_id=999, content="...")
if result['status'] == 'error':
    # Memory not found
    # Create new one instead
```

## Privacy & Security

- ❌ Never store API keys, passwords, or credentials
- ❌ Avoid storing personal identifiable information
- ✅ Store project context and technical decisions
- ✅ Store user preferences about code style
- ⚠️  Be mindful of sensitive project information

## Avoiding Memory Hallucinations

### The Risk
Old or incorrect memories can lead to outdated or wrong suggestions if not handled carefully.

### Best Practices to Prevent Hallucinations

1. **Always Verify with Current Code**
   - Don't blindly trust memories - check the actual codebase
   - Use memories as hints, not absolute truth
   - When in doubt, read the actual files

2. **Check Timestamps**
   - Pay attention to when memories were saved
   - Treat old memories (>1 month) with caution
   - Ask user if old information still applies

3. **Check Relevance Scores**
   - Scores < 0.02 are likely false positives
   - Low scores mean weak matches - verify carefully
   - High scores (> 0.03) are more reliable

4. **Update Outdated Memories**
   - When you discover information is outdated, update it immediately
   - Don't create duplicate memories - update the existing one
   - Example:
     ```python
     # Found outdated memory
     results = query_memory("database choice")
     if results[0]['timestamp'] < "2024-01-01":
         # Update with current information
         update_memory(doc_id=results[0]['id'], content="Updated: ...")
     ```

5. **Delete Incorrect Memories**
   - If a memory is wrong, delete it immediately
   - Don't let incorrect information persist
   - Add a new correct memory if needed

6. **Include Context in Memories**
   - Always note when and why decisions were made
   - Include relevant constraints or requirements
   - Example:
     ```
     ✅ Good: "Chose PostgreSQL on 2024-02-04 because we need JSONB support for user metadata in the v2 API"
     ❌ Bad: "Using PostgreSQL"
     ```

7. **Use Specific Queries**
   - Vague queries return vague results
   - Be specific about what you're looking for
   - Example:
     ```
     ✅ Good: "authentication flow for API endpoints"
     ❌ Bad: "auth"
     ```

8. **Cross-Reference Multiple Memories**
   - If multiple memories seem relevant, check for consistency
   - Conflicting memories indicate outdated information
   - Resolve conflicts before making suggestions

9. **When Unsure, Ask the User**
   - If memory seems outdated or unclear, ask for confirmation
   - Better to verify than to provide wrong information
   - Example: "I found a memory from 2 months ago saying X. Is this still accurate?"

10. **Regular Memory Maintenance**
    - Periodically review and clean up old memories
    - Update project-wide changes (migrations, refactors)
    - Archive or delete memories from completed features

### Warning Signs of Potential Hallucination

🚨 **Be extra careful when:**
- Memory is >1 month old
- Score is <0.02 (weak match)
- Memory lacks specific details or dates
- Multiple memories contradict each other
- Memory doesn't match what you see in the code
- User questions the accuracy of retrieved information

### Example: Proper Memory Verification

```python
# 1. Query memory
results = query_memory("database configuration")

# 2. Check the result
if results:
    memory = results[0]

    # Check timestamp
    if memory['timestamp'] < "2024-01-01":
        # Old memory - verify with user
        print("⚠️  Found old memory, verifying...")

    # Check score
    if memory['score'] < 0.02:
        # Weak match - might be false positive
        print("⚠️  Low relevance score, double-checking...")

    # 3. Cross-reference with actual code
    # Read database config files to verify

    # 4. If outdated, update it
    if outdated:
        update_memory(doc_id=memory['id'], content="Current info: ...")
```

---

## Part 2: Agenda Engine

### Purpose
The Agenda Engine allows AI agents to manage complex, multi-step workflows. Use it to:
- Create structured plans for achieving user goals.
- Track the progress of long-running tasks.
- Maintain a persistent "todo list" that carries over between sessions.
- Document acceptance criteria for individual steps.

### When to Use Agendas
- **Multi-step migrations**: e.g., "Move from Flask to FastAPI".
- **Feature implementation**: Breaking down a complex PR into smaller tasks.
- **Project milestones**: Tracking high-level progress.
- **System maintenance**: Scheduled tasks or cleanup activities.

### How to Structure Agendas

#### Agenda Level
- **Title**: Short, descriptive name (e.g., "Refactor Auth System").
- **Description**: Detailed overview of the goal and context. This field is indexed for full-text search.

#### Task Level
- **Details**: Specific instruction for this step.
- **Is Optional**: Set to `True` for tasks that are nice-to-have but don't block the agenda's completion.
- **Acceptance Guard**: Clear criteria/checks to verify the task is done (e.g., "Tests pass and coverage > 80%").

### How to Manage Agendas

#### 1. Create a Plan
Break down the goal into actionable tasks:
```python
create_agenda(
    title="Implement Vector Backfilling",
    description="Add a mechanism to ensure all memories have embeddings at startup.",
    tasks=[
        {"details": "Add model initialization before DB init", "is_optional": False},
        {"details": "Implement backfill loop in _init_db", "is_optional": False, "acceptance_guard": "Check for missing IDs in docs_vec"},
        {"details": "Add tests for backfilling logic", "is_optional": True}
    ]
)
```

#### 2. Track Progress
Update tasks as you complete them. The agenda will **automatically de-activate** once all non-optional tasks are finished.
```python
# Mark a task as completed
update_task(task_id=123, is_completed=True)
```

#### 3. Update or Expand
You can add tasks to an active agenda or update its metadata:
```python
update_agenda(
    agenda_id=1,
    new_tasks=[{"details": "Add logging to backfill loop"}],
    description="Updated: Including logging for better observability."
)
```

#### 4. Search and Retrieval
Search for existing plans by their description:
```python
# Find plans related to migrations
search_agendas("migration from flask")
```

### Best Practices

1. **Be Specific in Descriptions**: Since search is description-based, include relevant keywords (frameworks, module names, etc.).
2. **Use Acceptance Guards**: These serve as a "Definition of Done" for the AI, reducing ambiguity.
3. **Keep it Active**: Only keep relevant agendas active. Use `update_agenda(is_active=False)` to manually retire a plan if it's no longer needed.
4. **Link with Memories**: Reference relevant memory IDs in your agenda descriptions for better context linkage.
5. **Clean Up**: Delete inactive agendas if they are no longer useful for historical reference.

---

## Part 3: General Summary

**Key Points:**
1. Use descriptive categories (they're searchable!)
2. Keep topics short and descriptive
3. Make content detailed with context
4. Query before saving to avoid duplicates
5. Update instead of creating duplicates
6. Delete outdated information
7. Search works across category, topic, and content
8. Hybrid search understands both keywords and meaning

**Remember**: This is persistent storage across conversations. What you save now will be available in future sessions!
