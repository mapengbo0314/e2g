from typing import Tuple, List
from indexing.schema import FileSkeleton, FileEnrichment, ExportedSymbol, ImplementationInvariant

class MissingEnrichmentError(Exception):
    pass

class ASTMerger:
    @staticmethod
    def merge(file_path: str, skeleton: FileSkeleton, enrichment: FileEnrichment) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
        missing_ids = []
        final_symbols = []
        for sk_sym in skeleton.symbols:
            if sk_sym.id not in enrichment.symbols:
                missing_ids.append(sk_sym.id)
            else:
                en_sym = enrichment.symbols[sk_sym.id]
                final_symbols.append(ExportedSymbol(
                    id=sk_sym.id, name=sk_sym.name, signature=sk_sym.signature,
                    summary=en_sym.summary, file_path=file_path, line_number=sk_sym.line_number,
                    source_kind="merged"
                ))
                
        final_invariants = []
        for sk_inv in skeleton.invariants:
            if sk_inv.id not in enrichment.invariants:
                missing_ids.append(sk_inv.id)
            else:
                en_inv = enrichment.invariants[sk_inv.id]
                final_invariants.append(ImplementationInvariant(
                    id=sk_inv.id, primitive=sk_inv.primitive, intent=en_inv.intent,
                    usage_context=en_inv.usage_context, file_path=file_path, line_number=sk_inv.line_number,
                    evidence_origin="merged"
                ))
                
        if missing_ids:
            raise MissingEnrichmentError(f"Mandatory IDs missing from enrichment: {missing_ids}")
            
        return final_symbols, final_invariants
