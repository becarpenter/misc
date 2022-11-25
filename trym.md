```mermaid
flowchart LR
    D[draft-*] --> IETF[draft-ietf-*] --> WG[In progress in IETF WG] --> J[Apply judgment]
    D --> IRTF[draft-irtf-*] --> RG[Internet Research Task Force] --> J
    D --> IAB[draft-iab-*] --> B[Internet Architecture Board] --> J
    D --> X[draft-xyz-*] --> P[Personal work] --> J
```
