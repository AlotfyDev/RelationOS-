# Harvested Data

## Main Files
- `relations_harvested.parquet` - Primary relation dataset

## Data Schema
- `id` - Unique relation identifier
- `relation_name` - Name of the relation
- `domain` - Classification domain
- `source_standard` - Source specification
- `confidence` - Harvesting confidence score
- `harvested_at` - Timestamp of harvesting

## Usage
Load with pandas:
```python
import pandas as pd
df = pd.read_parquet('relations_harvested.parquet')
```
