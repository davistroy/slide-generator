# Workflow Visualization

## Complete Workflow

```mermaid
graph TD
    A[Topic Input] --> B[Research]
    B --> C{Checkpoint 1}
    C -->|Approved| D[Insight Extraction]
    C -->|Modify| B
    D --> E[Outline Generation]
    E --> F{Checkpoint 2}
    F -->|Approved| G[Content Drafting]
    F -->|Modify| E
    G --> H[Quality Analysis]
    H --> I[Content Optimization]
    I --> J{Checkpoint 3}
    J -->|Approved| K[Graphics Validation]
    J -->|Modify| G
    K --> L[Image Generation]
    L --> M[Visual Validation]
    M --> N{Checkpoint 4}
    N -->|Approved| O[PowerPoint Assembly]
    N -->|Regenerate| L
    O --> P[Final .pptx Output]

    style A fill:#e1f5fe
    style P fill:#c8e6c9
    style C fill:#fff3e0
    style F fill:#fff3e0
    style J fill:#fff3e0
    style N fill:#fff3e0
```

## Skill Dependencies

```mermaid
graph LR
    subgraph Research
        R1[research_skill]
        R2[insight_extraction_skill]
    end

    subgraph Content
        C1[outline_skill]
        C2[content_drafting_skill]
        C3[content_optimization_skill]
    end

    subgraph Visual
        V1[graphics_validation_skill]
        V2[image_generation_skill]
        V3[visual_validation_skill]
    end

    subgraph Assembly
        A1[powerpoint_builder]
    end

    R1 --> R2
    R2 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> V1
    V1 --> V2
    V2 --> V3
    V3 --> A1
```

## ASCII Workflow Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                    Presentation Generation Workflow                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐  │
│   │  Topic  │───▶│ Research │───▶│ Insights │───▶│   Outline   │  │
│   └─────────┘    └──────────┘    └──────────┘    └─────────────┘  │
│                       │                                │           │
│                       ▼                                ▼           │
│                  ☐ Checkpoint 1                   ☐ Checkpoint 2   │
│                                                                     │
│   ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐  │
│   │  .pptx  │◀───│ Assembly │◀───│  Images  │◀───│   Content   │  │
│   └─────────┘    └──────────┘    └──────────┘    └─────────────┘  │
│                                       │                │           │
│                                       ▼                ▼           │
│                                  ☐ Checkpoint 4   ☐ Checkpoint 3   │
│                                                                     │
│   Legend:  ───▶ Flow    ☐ Human Checkpoint                         │
└────────────────────────────────────────────────────────────────────┘
```
