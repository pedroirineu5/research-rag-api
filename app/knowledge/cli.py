import argparse
import os
from pathlib import Path

from openai import OpenAI
from sqlalchemy import select

from app.db import SessionLocal
from app.knowledge.models import Document, RpgSystem
from app.knowledge.service import ingest_pdf, register_system


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gerenciar livros de regras de RPG")
    commands = parser.add_subparsers(dest="command", required=True)

    register = commands.add_parser("register", help="Cadastrar um sistema")
    register.add_argument("--slug", required=True)
    register.add_argument("--name", required=True)
    register.add_argument("--language", required=True)
    register.add_argument("--response-language", default="pt-BR")

    ingest = commands.add_parser("ingest", help="Enviar PDF ao Vector Store")
    ingest.add_argument("--slug", required=True)
    ingest.add_argument("--pdf", required=True, type=Path)

    commands.add_parser("list", help="Listar sistemas e documentos")
    args = parser.parse_args(argv)

    if args.command == "ingest" and not os.environ.get("OPENAI_API_KEY"):
        parser.error("configure OPENAI_API_KEY no .env antes da ingestão")

    with SessionLocal() as db:
        if args.command == "register":
            system = register_system(
                db,
                slug=args.slug,
                name=args.name,
                language=args.language,
                response_language=args.response_language,
            )
            print(f"Sistema cadastrado: {system.slug} ({system.name})")
        elif args.command == "ingest":
            document = ingest_pdf(
                db, slug=args.slug, pdf_path=args.pdf, client=OpenAI()
            )
            print(
                f"Documento {document.id}: {document.status}, "
                f"file_id={document.file_id}"
            )
        else:
            systems = db.scalars(select(RpgSystem).order_by(RpgSystem.slug)).all()
            for system in systems:
                print(
                    f"{system.slug}\t{system.name}\t{system.language}\t"
                    f"{system.response_language}\t"
                    f"{system.vector_store_id or '-'}"
                )
                documents = db.scalars(
                    select(Document)
                    .where(Document.system_id == system.id)
                    .order_by(Document.id)
                )
                for document in documents:
                    print(
                        f"  {document.id}\t{document.filename}\t"
                        f"{document.status}\t{document.file_id or '-'}"
                    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
