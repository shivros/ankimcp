# AnkiMCP Permission System

AnkiMCP provides a comprehensive permission system to control AI access to your Anki collection. This allows you to protect sensitive decks, prevent unwanted modifications, and maintain control over your learning data.

## Overview

The permission system operates at multiple levels:
- **Global permissions**: Enable/disable read, write, and delete operations globally
- **Deck permissions**: Control access to specific decks using allowlists or denylists
- **Tag restrictions**: Protect notes with specific tags from modification
- **Note type permissions**: Control which note types can be created or modified

## Configuration

Permissions are configured in Anki's addon configuration. Go to Tools → Add-ons → AnkiMCP → Config to modify settings.

### Basic Structure

```json
{
  "permissions": {
    "global": {
      "read": true,
      "write": true,
      "delete": true
    },
    "mode": "allowlist",
    "deck_permissions": {
      "allowlist": [],
      "denylist": []
    },
    "protected_decks": ["Default"],
    "tag_restrictions": {
      "protected_tags": [],
      "readonly_tags": []
    },
    "note_type_permissions": {
      "allow_create": true,
      "allow_modify": false,
      "allowed_types": []
    }
  }
}
```

## Permission Modes

### Allowlist Mode
In allowlist mode, only explicitly listed decks can be accessed:
```json
{
  "mode": "allowlist",
  "deck_permissions": {
    "allowlist": ["Spanish", "French", "Study::*"],
    "denylist": []
  }
}
```

### Denylist Mode
In denylist mode, all decks are accessible except those explicitly denied:
```json
{
  "mode": "denylist",
  "deck_permissions": {
    "allowlist": [],
    "denylist": ["Personal::*", "Work::Confidential"]
  }
}
```

## Configuration Options

### Global Permissions
Control overall access levels:
```json
"global": {
  "read": true,    // Allow reading any data
  "write": true,   // Allow creating/modifying notes
  "delete": false  // Prevent deletion of any notes
}
```

### Deck Permissions
Use glob patterns to match deck names:
```json
"deck_permissions": {
  "allowlist": [
    "Language::*",           // All language learning decks
    "Study::Public::*",      // Public study materials
    "Shared"                 // Specific deck
  ],
  "denylist": [
    "Personal::*",          // All personal decks
    "*.Private",            // Decks ending with .Private
    "Work::Confidential::*" // Confidential work materials
  ]
}
```

### Protected Decks
Decks that cannot be modified or deleted:
```json
"protected_decks": [
  "Default",
  "Core 2000",
  "Medical::Reference"
]
```

### Tag Restrictions
Control access based on note tags:
```json
"tag_restrictions": {
  "protected_tags": ["important", "exam", "final"],  // Cannot modify/delete
  "readonly_tags": ["archive", "reference"]          // Can only read
}
```

### Note Type Permissions
Control which note types can be used:
```json
"note_type_permissions": {
  "allow_create": true,              // Allow creating new note types
  "allow_modify": false,             // Prevent modifying existing note types
  "allowed_types": ["Basic", "Cloze"] // Only allow specific note types
}
```

## Use Cases

### 1. Study Assistant (Read-Only)
Allow AI to help review but not modify:
```json
{
  "global": {
    "read": true,
    "write": false,
    "delete": false
  }
}
```

### 2. Language Learning Assistant
Allow modifications only to language decks:
```json
{
  "mode": "allowlist",
  "deck_permissions": {
    "allowlist": ["Spanish", "French", "German", "Languages::*"]
  },
  "protected_decks": ["Languages::Core"]
}
```

### 3. Collaborative Study
Allow modifications but protect important content:
```json
{
  "mode": "denylist",
  "deck_permissions": {
    "denylist": ["Personal::*", "Private::*"]
  },
  "tag_restrictions": {
    "protected_tags": ["final-exam", "verified"],
    "readonly_tags": ["professor-notes"]
  }
}
```

### 4. Content Creation
Allow creating notes in specific decks only:
```json
{
  "global": {
    "read": true,
    "write": true,
    "delete": false
  },
  "mode": "allowlist",
  "deck_permissions": {
    "allowlist": ["AI-Generated::*", "To-Review::*"]
  },
  "note_type_permissions": {
    "allowed_types": ["Basic", "Basic (and reversed card)"]
  }
}
```

## Security Best Practices

1. **Start Restrictive**: Begin with minimal permissions and expand as needed
2. **Use Protected Decks**: Mark important decks as protected to prevent accidental modification
3. **Tag Important Notes**: Use protected tags for critical study materials
4. **Regular Reviews**: Periodically review AI-created content in dedicated decks
5. **Backup First**: Always backup your collection before enabling write permissions

## Permission Precedence

Permissions are evaluated in this order:
1. Global permissions (if disabled globally, operation is denied)
2. Protected decks (always deny modifications)
3. Tag restrictions (protected > readonly > normal)
4. Deck allowlist/denylist
5. Note type restrictions

The most restrictive permission wins.

## Checking Current Permissions

To see the current permission configuration, the AI can use the `get_permissions` tool:
```
AI: Let me check what permissions I have...
[Uses get_permissions tool]
```

This will show:
- Current mode (allowlist/denylist)
- Global permission settings
- Protected decks
- Configured allowlists/denylists
- Tag restrictions
- Note type permissions

## Troubleshooting

### AI Can't Access a Deck
1. Check if you're in allowlist mode and the deck isn't listed
2. Check if the deck matches a denylist pattern
3. Verify global read permission is enabled

### AI Can't Create Notes
1. Check global write permission
2. Verify the target deck isn't protected
3. Check deck is in allowlist (if using allowlist mode)
4. Verify note type is allowed

### AI Can't Delete Notes
1. Check global delete permission
2. Verify the note doesn't have protected tags
3. Check the note's deck isn't protected

## Examples

### Minimal Read-Only Access
```json
{
  "permissions": {
    "global": {
      "read": true,
      "write": false,
      "delete": false
    }
  }
}
```

### Full Access to Specific Decks
```json
{
  "permissions": {
    "mode": "allowlist",
    "deck_permissions": {
      "allowlist": ["AI-Study::*", "Shared::*"]
    }
  }
}
```

### Protect Personal Content
```json
{
  "permissions": {
    "mode": "denylist",
    "deck_permissions": {
      "denylist": ["Personal::*", "Work::*", "*.Private"]
    },
    "tag_restrictions": {
      "protected_tags": ["personal", "confidential", "work"]
    }
  }
}
```
