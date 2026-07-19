# STIX Threat Intel → Network Graph Mapping

Maps OpenCTI STIX campaign data to force-directed graph nodes and edges for cybersecurity intelligence dashboards.

## Entity types (from real OpenCTI data)

| STIX Type | Graph Node | Color | Display label | Key metadata |
|---|---|---|---|---|
| `Campaign` | Campaign | `#ef4444` (red) | Campaign | first_seen, last_seen, confidence |
| `Attack-Pattern` | TTP | `#eab308` (yellow) | TTP | external_id (e.g. T1190), tactic |
| `Malware` | Malware | `#f97316` (orange) | Malware | malware_types, aliases |
| `Intrusion-Set` | Threat Actor | `#8b5cf6` (purple) | Threat Actor | aliases, sophistication |
| `Vulnerability` | CVE | `#ec4899` (pink) | CVE | score (from metrics), type |
| `Tool` | Tool | `#06b6d4` (cyan) | Tool | tool_types, version |
| `Location` | Location | `#10b981` (green) | Location | region, target_sector |
| `Identity` | Organization | `#3b82f6` (blue) | Organization | identity_class, sector |

## STIX relationship types

| `relationship_type` | Edge label | Semantic |
|---|---|---|
| `uses` | uses | Campaign/TTP uses tool or technique |
| `attributed-to` | attributed to | Points to threat actor |
| `targets` | targets | Targets location, identity, sector |
| `mitigates` | mitigates | Mitigation for technique/vulnerability |
| `exploits` | exploits | TTP exploits vulnerability |
| `indicates` | indicates | IOC/indicator points to TTP |
| `investigates` | investigates | Report investigates TTP/campaign |

## Data structure from OpenCTI GraphQL

Campaigns query returns nested edges:

```json
{
  "data": {
    "campaigns": {
      "edges": [
        {
          "node": {
            "id": "9e45623c...",
            "standard_id": "campaign--285694c9...",
            "entity_type": "Campaign",
            "name": "Oldsmar Treatment Plant Intrusion",
            "description": "...",
            "first_seen": "2021-02-01T05:00:00.000Z",
            "last_seen": "2021-02-01T05:00:00.000Z",
            "confidence": 75,
            "externalReferences": {
              "edges": [
                {
                  "node": {
                    "source_name": "mitre-attack",
                    "url": "https://attack.mitre.org/campaigns/C0009",
                    "external_id": "C0009"
                  }
                }
              ]
            },
            "stixCoreRelationships": {
              "edges": [
                {
                  "node": {
                    "id": "...",
                    "entity_type": "stix-core-relationship",
                    "relationship_type": "uses",
                    "from": { "id": "...", "entity_type": "Attack-Pattern", "name": "..." },
                    "to": { "id": "...", "entity_type": "Malware", "name": "..." }
                  }
                }
              ]
            },
            "numberOfConnectedElement": 6,
            "objectMarking": [...],
            "createdBy": { "name": "The MITRE Corporation", "entity_type": "Organization" }
          }
        }
      ],
      "pageInfo": { ... }
    }
  }
}
```

## Graph build sequence

```
Campaigns query
       ↓
   Extract stixCoreRelationships.edges[].node
       ↓
   For each relationship, resolve `from` and `to` entities
       ↓
   Deduplicate by entity id (same entity may appear in multiple relationships)
       ↓
   Map each entity → GraphNode with color + metadata
       ↓
   Map each relationship → GraphLink with relationship_type as label
       ↓
   Feed { nodes, links } to force-graph
```

## Display per entity type (what analysts need to see)

| Entity | Show on node | Hide in tooltip/popup |
|---|---|---|
| Campaign | first_seen, last_seen, confidence | description, externalReferences |
| Attack-Pattern | MITRE ID (e.g. T1190), tactic | description, detection |
| Malware | Type, aliases | description, platforms |
| Intrusion-Set | Aliases, sophistication level | description, associated campaigns |
| Vulnerability | CVE ID, CVSS score | affected software, description |
| Tool | Category | description, references |

Use node `val` for visual weight: Campaign nodes get 30 (largest), relations 15-20, metadata entities 12-15.

## Real data considerations

- OpenCTI returns edge connection for relationships — not resolved entity name on same node. You need to either fetch related entities separately or request them inline with a deeper GraphQL query.
- `externalReferences` contain MITRE ATT&CK pages as `external_id` (C0009 for campaigns, T1190 for techniques).
- `objectMarking` contains access/classification markings — filter by the user's clearance if applicable.
- `numberOfConnectedElement` is a rough importance signal — higher = more connected = potentially more important node.
- `first_seen`/`last_seen` can be identical (single-incident campaigns).
