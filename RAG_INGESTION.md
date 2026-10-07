

# Ingestion Process

The ingestion process of the manuals tries to leverage the manual strcuture to properly extract textual relevant chunks, instead of simply extracting raw text from the file

## PDF Parsing

### Outline

The provided manuals were writen using a outline (which are basically file anotations in metadata). They consist on chapters, sections and subsections. Those can be read using PdfReader library.

A function walks the pdf outline and extracts its reference, title and a reference to its starting page

### Boilerplate Striping

Every page of a manual repeats the same ownership notice and running header/footer. A line is flagged as boilerplate when its normalised form shows up on at least 40% of the pages (`BOILERPLATE_PAGE_SHARE`). Normalisation strips a leading or trailing page number (arabic or roman) first, so e.g. "12 SAFETY INSTRUCTIONS" and "13 SAFETY INSTRUCTIONS" are still recognised as the same repeated line even though the page number changes from page to page.

### Table of Contents Removal

Pages that are dominated by dotted-leader lines ("8.3 INSTALLATION ......... 34") are detected as tables of contents (`is_toc_page`) and emptied out: a TOC has no content worth embedding, and left in place it would otherwise get chunked into noise. Its page is kept in the page list (so page numbers elsewhere stay correct), just with no text.

`searchable_pages` is the entry point used by ingestion: it strips boilerplate first, then empties TOC pages, producing the text that actually gets chunked.

## Chunking

### Section Assignment

Outline entries are turned into `Section` objects, each carrying a breadcrumb `path` built from the stack of ancestor titles, e.g. `"4 CLOSING MACHINE DESCRIPTION > 4.3 TECHNICAL DATA"`. `assign_sections` locates each section's heading inside its starting page and slices the concatenated page stream so a section's text runs from its own heading up to the next heading in document order — a parent section's text therefore stops where its first child section begins.

### Splitting into Chunks

Within a section, text is first split into units that must stay intact: wrapped lines are rejoined into full sentences, while short lines (list items, table cells, standalone headings) are kept as their own unit so tables aren't reflowed into prose.

Units are then packed into chunks of about 200 words (`TARGET_WORDS`), capped at 280 words (`MAX_WORDS`). The last unit of a chunk is carried over as the first unit of the next one, giving each chunk a small overlap with its neighbour. Chunks shorter than 12 words (`MIN_CHUNK_WORDS`) are dropped as heading-only noise.

Every resulting `Chunk` keeps its section number, title, breadcrumb path and page range, so a retrieved chunk can be cited back as, for example, "section 11.5.1.5, page 94".

## Embedding Extraction

Once a manual is chunked, `index_manual` (`ingest.py`) embeds `chunk.embedding_text` for every chunk rather than the raw content — that property prefixes the chunk with its breadcrumb path, so the embedding captures the section context along with the paragraph itself.

Embeddings are produced by `app.rag.embeddings` using fastembed (ONNX runtime, no torch) with `BAAI/bge-base-en-v1.5`, a 768-dimension model matching the `VECTOR(768)` column in `schema.sql`. Chunks are embedded in batches of 64 (`_EMBED_BATCH`) to bound memory use on large manuals. fastembed is CPU-bound and synchronous, so each batch runs in a worker thread rather than blocking the event loop.

The model is loaded lazily on first use and cached for the lifetime of the process (`lru_cache`), so the cost of loading its weights is paid once per process, not once per manual.

### Why `bge-base-en-v1.5`

- **CPU-only, no GPU dependency.** fastembed runs the model through ONNX runtime, which fits a service where ingestion runs as a batch job rather than something provisioned with a GPU.
- **Retrieval quality over raw speed.** Search in this system never compares vectors across more than a few hundred rows (one manual at a time, no ANN index — see Idempotency/schema notes above), so embedding and scan cost are negligible regardless of model size. That removes the usual incentive to reach for a smaller model, so the choice can be made on retrieval quality alone, and `bge-base` scores meaningfully better than the small variant on retrieval benchmarks (MTEB).
- **Matches the content.** Manual text is long, technical, English-only, with multi-level section numbering; precision at the embedding level reduces the chance of a query landing on the wrong subsection.
- **Asymmetric encoding.** Like the rest of the `bge` family, it's trained with distinct query/passage representations, which fastembed exposes as separate `passage_embed` (ingest) / `query_embed` (search) calls — matching the ingest/search split already in this codebase.
- **Storage cost is acceptable.** 768-dim vectors are double the size of the `small` variant's 384, but against a few hundred chunks per manual that's a negligible amount of storage for the quality gained.

## Idempotency

Before reparsing a manual, `index_manual` hashes its raw PDF bytes (sha256) and compares that hash, together with the embedding model name and `CHUNKER_VERSION`, against the `manual_index` table. If all three already match, the manual is skipped entirely. This makes re-running ingestion over the whole bucket cheap, while bumping the chunker version or switching embedding models forces every manual to be reprocessed.

When a manual is (re)indexed, its previous chunks are deleted and the new ones inserted inside a single transaction, so readers never observe a manual half re-indexed.
