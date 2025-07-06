# Document Filtering System

## Overview

The RAG Complete system provides comprehensive document filtering capabilities that allow users to efficiently organize, search, and manage their document collections. This document outlines all available filtering features and how to use them.

## Features Overview

### 🗂️ **Document Groups/Collections**
- Organize documents into logical groups
- Hierarchical grouping support
- Color-coded categories for visual organization
- Default groups: Financial Reports, Legal Documents, HR Documents, Technical Documentation, Marketing Materials

### 🏷️ **Document Tags**
- Flexible tagging system for metadata
- Popular tags: urgent, important, draft, reviewed, confidential, archived, public, internal
- Auto-complete tag suggestions
- Tag usage statistics

### 🔍 **Advanced Search & Filtering**
- Full-text search across filenames, titles, authors, and tags
- Metadata filtering (file type, size, page count, language, author)
- Date range filtering (creation/modification dates)
- Custom metadata filtering
- Multiple sorting options

### 📋 **Bulk Operations**
- Apply tags to multiple documents
- Move documents between groups
- Batch delete operations
- Tag/untag multiple documents

## API Endpoints

### Document Groups API

#### Create Document Group
```http
POST /api/document-groups/
Content-Type: application/json

{
  "name": "Financial Reports",
  "description": "Quarterly and annual financial reports",
  "color": "#3B82F6",
  "icon": "chart-bar",
  "parent_id": null
}
```

#### List Document Groups
```http
GET /api/document-groups/?include_empty=true
```

#### Get Group Hierarchy
```http
GET /api/document-groups/hierarchy
```

#### Update Document Group
```http
PUT /api/document-groups/{group_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "color": "#EF4444"
}
```

#### Delete Document Group
```http
DELETE /api/document-groups/{group_id}?force=false
```

### Document Tags API

#### Create Document Tag
```http
POST /api/document-tags/
Content-Type: application/json

{
  "name": "urgent",
  "color": "#EF4444"
}
```

#### List Document Tags
```http
GET /api/document-tags/?include_unused=true
```

#### Get Popular Tags
```http
GET /api/document-tags/popular?limit=10
```

#### Search Tags
```http
GET /api/document-tags/search?query=urgent&limit=10
```

#### Update Document Tag
```http
PUT /api/document-tags/{tag_id}?name=new-name&color=#10B981
```

#### Delete Document Tag
```http
DELETE /api/document-tags/{tag_id}?force=false
```

### Enhanced Documents API

#### Upload Document with Metadata
```http
POST /api/documents/upload
Content-Type: multipart/form-data

file: [FILE]
group_id: group_financial
tags: urgent,q3-2024,reviewed
custom_metadata: {"department": "finance", "confidentiality": "internal"}
```

#### Advanced Document Filtering
```http
POST /api/documents/filter
Content-Type: application/json

{
  "search_query": "financial report",
  "status": ["completed"],
  "file_type": ["pdf"],
  "group_id": ["group_financial"],
  "tags": ["urgent"],
  "created_after": "2023-01-01T00:00:00Z",
  "created_before": "2023-12-31T23:59:59Z",
  "min_size": 1000000,
  "max_size": 50000000,
  "min_pages": 1,
  "max_pages": 100,
  "language": ["en"],
  "author": ["John Doe"],
  "custom_filters": {
    "department": "finance",
    "confidentiality": "internal"
  },
  "sort_by": "created_at",
  "sort_order": "desc"
}
```

#### Get Available Filters
```http
GET /api/documents/filters/available
```

Response:
```json
{
  "file_types": ["pdf", "docx", "pptx"],
  "statuses": ["completed", "processing", "failed"],
  "groups": [
    {
      "id": "group_financial",
      "name": "Financial Reports",
      "color": "#3B82F6"
    }
  ],
  "tags": [
    {
      "id": "tag_urgent",
      "name": "urgent",
      "color": "#EF4444"
    }
  ],
  "languages": ["en", "es", "fr"],
  "authors": ["John Doe", "Jane Smith"],
  "date_range": {
    "earliest": "2023-01-01T00:00:00Z",
    "latest": "2023-12-31T23:59:59Z"
  },
  "size_range": {
    "min": 1024,
    "max": 50000000
  }
}
```

#### Update Document Tags
```http
PUT /api/documents/{document_id}/tags
Content-Type: application/json

["urgent", "reviewed", "q3-2024"]
```

#### Update Document Group
```http
PUT /api/documents/{document_id}/group
Content-Type: application/json

"group_financial"
```

#### Bulk Operations
```http
POST /api/documents/bulk
Content-Type: application/json

{
  "document_ids": ["doc_123", "doc_456"],
  "operation": "tag",
  "tag_ids": ["tag_urgent", "tag_reviewed"]
}
```

Supported operations:
- `tag`: Add tags to documents
- `untag`: Remove tags from documents
- `group`: Move documents to a group
- `delete`: Delete multiple documents

## Filter Types

### Text Search
- **Field**: `search_query`
- **Description**: Search across filename, title, author, and tags
- **Example**: `"financial report Q3"`

### Status Filtering
- **Field**: `status`
- **Options**: `pending`, `processing`, `completed`, `failed`
- **Type**: Array of statuses

### File Type Filtering
- **Field**: `file_type` 
- **Options**: `pdf`, `docx`, `pptx`, `txt`, `md`
- **Type**: Array of file types

### Group Filtering
- **Field**: `group_id`
- **Description**: Filter by document groups
- **Type**: Array of group IDs

### Tag Filtering
- **Field**: `tags`
- **Description**: Filter by document tags
- **Type**: Array of tag names

### Date Range Filtering
- **Fields**: 
  - `created_after` / `created_before`
  - `updated_after` / `updated_before`
- **Format**: ISO 8601 datetime strings
- **Example**: `"2023-01-01T00:00:00Z"`

### Size Filtering
- **Fields**: `min_size` / `max_size`
- **Unit**: Bytes
- **Example**: `1048576` (1MB)

### Metadata Filtering
- **Fields**: 
  - `min_pages` / `max_pages`: Page count filtering
  - `language`: Document language
  - `author`: Document author
- **Type**: Arrays for multi-value fields

### Custom Metadata Filtering
- **Field**: `custom_filters`
- **Description**: Filter by custom metadata fields
- **Type**: Object with key-value pairs
- **Example**: `{"department": "finance", "confidentiality": "internal"}`

## Sorting Options

### Available Sort Fields
- `created_at`: Creation date (default)
- `updated_at`: Last modification date
- `filename`: Document filename
- `size`: File size
- `pages`: Page count
- `status`: Processing status

### Sort Orders
- `desc`: Descending (default)
- `asc`: Ascending

## Frontend Integration

### Filter Components

#### Search Bar
```typescript
const [searchQuery, setSearchQuery] = useState('')

const handleSearch = () => {
  applyFilters({ search_query: searchQuery })
}
```

#### Group Filter
```typescript
const [selectedGroups, setSelectedGroups] = useState<string[]>([])

const handleGroupChange = (groupIds: string[]) => {
  setSelectedGroups(groupIds)
  applyFilters({ group_id: groupIds })
}
```

#### Tag Filter
```typescript
const [selectedTags, setSelectedTags] = useState<string[]>([])

const handleTagChange = (tags: string[]) => {
  setSelectedTags(tags)
  applyFilters({ tags })
}
```

#### Date Range Filter
```typescript
const [dateRange, setDateRange] = useState({
  created_after: null,
  created_before: null
})

const handleDateRangeChange = (range: DateRange) => {
  setDateRange(range)
  applyFilters(range)
}
```

### Filter Presets

#### Popular Presets
- **Recent Documents**: `sort_by: "created_at", sort_order: "desc"`
- **Urgent Items**: `tags: ["urgent"]`
- **Large Files**: `min_size: 10485760` (10MB+)
- **PDFs Only**: `file_type: ["pdf"]`
- **This Month**: `created_after: "2023-11-01T00:00:00Z"`

#### Custom Presets
Users can save their frequently used filter combinations as custom presets.

## Best Practices

### Performance Optimization
1. **Use specific filters** to reduce result sets
2. **Implement pagination** for large document collections
3. **Cache filter options** to reduce API calls
4. **Debounce search inputs** to avoid excessive queries

### User Experience
1. **Show filter counts** next to each option
2. **Provide clear filter reset** functionality
3. **Display active filters** prominently
4. **Enable filter persistence** across sessions

### Data Organization
1. **Use consistent naming** for groups and tags
2. **Implement tag hierarchies** for complex categorizations
3. **Regular cleanup** of unused tags and empty groups
4. **Document metadata standards** for your organization

## Error Handling

### Common Error Scenarios
- **Invalid filter values**: Return 400 with specific error message
- **Non-existent group/tag IDs**: Return 404 with helpful suggestions
- **Permission errors**: Return 403 with clear explanation
- **Rate limiting**: Return 429 with retry information

### Frontend Error Display
```typescript
const handleFilterError = (error: FilterError) => {
  if (error.code === 'INVALID_GROUP') {
    toast.error(`Group "${error.value}" not found`)
    // Remove invalid group from filters
    removeInvalidFilters(['group_id'], [error.value])
  }
}
```

## Migration Guide

### From Basic to Advanced Filtering

1. **Update API calls** to use new filter endpoints
2. **Migrate existing tags** to new tag system
3. **Create default groups** for document organization
4. **Update frontend components** to use new filter UI
5. **Train users** on new filtering capabilities

### Data Migration
```sql
-- Example migration for existing systems
INSERT INTO document_groups (id, name, description, color)
VALUES 
  ('group_default', 'Uncategorized', 'Documents without specific category', '#6B7280');

UPDATE documents 
SET group_id = 'group_default' 
WHERE group_id IS NULL;
```

## Analytics & Reporting

### Filter Usage Metrics
- Most used filter combinations
- Popular search queries
- Group and tag usage statistics
- User filtering patterns

### Performance Metrics
- Filter response times
- Cache hit rates
- Database query performance
- User satisfaction scores

## Future Enhancements

### Planned Features
- **AI-powered auto-tagging** based on content analysis
- **Smart group suggestions** using machine learning
- **Advanced metadata extraction** from document content
- **Collaborative filtering** with team recommendations
- **Document similarity clustering** for better organization

### API Versioning
The filtering API is designed with extensibility in mind. Future versions will maintain backward compatibility while adding new capabilities.

---

For technical support or feature requests, please refer to the main project documentation or contact the development team. 