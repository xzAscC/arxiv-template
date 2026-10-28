# Search arxiv/ so a conference version beside it (e.g. iclr2027/main.tex) names the shared
# files by bare name, as arxiv/main.tex does:
#   \input{macro}  \input{sections/introduction}  \bibliography{reference}
# Overleaf reads this file from the project root. Locally, ~/.config/latexmk/latexmkrc
# runs it when you compile in any subfolder.
use Cwd qw(abs_path);
use File::Basename qw(dirname);
my $root = dirname(abs_path(__FILE__));
ensure_path('TEXINPUTS', "$root/arxiv");
ensure_path('BIBINPUTS', "$root/arxiv");
# Then put the current folder in front (ensure_path prepends), so a conference version's own
# main.tex or macro.tex is never replaced by arxiv/'s file of the same name.
ensure_path('TEXINPUTS', '.');
ensure_path('BIBINPUTS', '.');
