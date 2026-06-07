import os
import click
from app import pdf_to_long_image

@click.command()
@click.option('--input-dir', default='./inputs', help='Directory containing input PDF files.')
@click.option('--output-dir', default='./outputs', help='Directory to save converted images.')
@click.option('--format', 'output_format', default='tiff', type=click.Choice(['tiff', 'png', 'jpeg'], case_sensitive=False), help='Output image format.')
@click.option('--dpi', default=200, help='Resolution DPI for the conversion.')
def main(input_dir, output_dir, output_format, dpi):
    """Batch convert PDF files in a directory to single long images."""
    if not os.path.exists(input_dir):
        click.echo(f"Error: Input directory '{input_dir}' does not exist.")
        exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # Scan for all PDF files (case-insensitive)
    files = os.listdir(input_dir)
    pdf_files = [f for f in files if f.lower().endswith(".pdf")]

    if not pdf_files:
        click.echo(f"No PDF files found in '{input_dir}'.")
        exit(0)

    click.echo(f"Found {len(pdf_files)} PDF file(s) in '{input_dir}'. Starting batch conversion...")

    successes = []
    failures = []
    
    ext_map = {'tiff': 'tiff', 'png': 'png', 'jpeg': 'jpg'}
    file_ext = ext_map.get(output_format.lower(), 'tiff')

    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        base_name = os.path.splitext(pdf_file)[0]
        output_filename = f"{base_name}_long_image.{file_ext}"
        output_path = os.path.join(output_dir, output_filename)

        click.echo("\n" + "="*60)
        click.echo(f"Processing: {pdf_file}")
        click.echo("="*60)

        try:
            if pdf_to_long_image(pdf_path, output_path, output_format, dpi):
                successes.append(pdf_file)
                click.echo(f"Success! Saved long image to: {output_path}")
            else:
                failures.append((pdf_file, "No pages extracted"))
        except Exception as e:
            click.echo(f"Error converting '{pdf_file}': {e}")
            failures.append((pdf_file, str(e)))

    click.echo("\n" + "="*60)
    click.echo("BATCH PROCESSING SUMMARY")
    click.echo("="*60)
    click.echo(f"Total PDFs found: {len(pdf_files)}")
    click.echo(f"Successfully converted: {len(successes)}")
    click.echo(f"Failed to convert: {len(failures)}")

    if successes:
        click.echo("\nSuccessful conversions:")
        for s in successes:
            click.echo(f"  - {s}")

    if failures:
        click.echo("\nFailed conversions:")
        for f, err in failures:
            click.echo(f"  - {f}: {err}")

if __name__ == '__main__':
    main()
