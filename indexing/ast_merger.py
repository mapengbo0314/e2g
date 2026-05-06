from typing import Tuple, List
from indexing.schema import FileSkeleton, FileEnrichment, ExportedSymbol, ImplementationInvariant
import logging

class MissingEnrichmentError(Exception):
    pass

class ASTMerger:
    @staticmethod
    def merge(file_path: str, skeleton: FileSkeleton, enrichment: FileEnrichment) -> Tuple[List[ExportedSymbol], List[ImplementationInvariant]]:
        final_symbols = []
        
        # Process all symbols from the skeleton
        for sk_sym in skeleton.symbols:
            if sk_sym.id not in enrichment.symbols:
                logging.warning(f"Symbol {sk_sym.id} missing from enrichment for {file_path}")
                final_symbols.append(ExportedSymbol(
                    id=sk_sym.id, name=sk_sym.name, is_private=sk_sym.is_private, signature=sk_sym.signature,
                    summary=getattr(sk_sym, 'summary', ''), file_path=file_path, line_number=sk_sym.line_number,
                    source_kind="ast_fallback"
                ))
            else:
                # Combine skeleton data with LLM enrichment
                en_sym = enrichment.symbols[sk_sym.id]
                final_symbols.append(ExportedSymbol(
                    id=sk_sym.id, name=sk_sym.name, is_private=sk_sym.is_private, signature=sk_sym.signature,
                    summary=en_sym.summary, file_path=file_path, line_number=sk_sym.line_number,
                    source_kind="merged"
                ))
                
        final_invariants = []
        # Process all invariants from the skeleton
        for sk_inv in skeleton.invariants:
            if sk_inv.id not in enrichment.invariants:
                logging.warning(f"Invariant {sk_inv.id} missing from enrichment for {file_path}")
                final_invariants.append(ImplementationInvariant(
                    id=sk_inv.id, primitive=sk_inv.primitive, intent=getattr(sk_inv, 'intent', ''),
                    usage_context=getattr(sk_inv, 'usage_context', ''), file_path=file_path, line_number=sk_inv.line_number,
                    evidence_origin="merged"
                ))
            else:
                # Combine invariant skeleton with LLM enrichment
                en_inv = enrichment.invariants[sk_inv.id]
                final_invariants.append(ImplementationInvariant(
                    id=sk_inv.id, primitive=sk_inv.primitive, intent=en_inv.intent,
                    usage_context=en_inv.usage_context, file_path=file_path, line_number=sk_inv.line_number,
                    evidence_origin="merged"
                ))
                
        return final_symbols, final_invariants
