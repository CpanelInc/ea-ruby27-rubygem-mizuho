# Defining the package namespace
%global ns_name ea
%global ns_dir /opt/cpanel
%global pkg ruby27
%global gem_name mizuho

%global ruby_version %(/opt/cpanel/ea-ruby27/root/usr/bin/ruby -e 'puts %RUBY_VERSION')

# Force Software Collections on
%global _scl_prefix %{ns_dir}
%global scl %{ns_name}-%{pkg}
# HACK: OBS Doesn't support macros in BuildRequires statements, so we have
#       to hard-code it here.
# https://en.opensuse.org/openSUSE:Specfile_guidelines#BuildRequires
%global scl_prefix %{scl}-
%{?scl:%scl_package rubygem-%{gem_name}}

# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4590 for more details
%define release_prefix 6

# Although there are tests, they don't work yet
# https://github.com/FooBarWidget/mizuho/issues/5
%global enable_tests 0

%if 0%{?rhel} >= 8
# NOTE: our macros.scl insists that I use python3.  Too much risk on the
# scripts
%global __os_install_post %{expand:
    /usr/lib/rpm/brp-scl-compress %{_scl_root}
    %{!?__debug_package:/usr/lib/rpm/brp-strip %{__strip}
    /usr/lib/rpm/brp-strip-comment-note %{__strip} %{__objdump}
    }
    /usr/lib/rpm/brp-strip-static-archive %{__strip}
    /usr/lib/rpm/brp-scl-python-bytecompile /usr/bin/python2 %{?_python_bytecompile_errors_terminate_build} %{_scl_root}
    /usr/lib/rpm/brp-python-hardlink
%{nil}}
%endif

Summary:       Mizuho documentation formatting tool
Name:          %{?scl:%scl_prefix}rubygem-%{gem_name}
Version:       0.9.20
Release:       %{release_prefix}%{?dist}.cpanel
Group:         Development/Languages
License:       MIT
URL:           https://github.com/FooBarWidget/mizuho
Source0:       https://rubygems.org/gems/%{gem_name}-%{version}.gem
Patch1:        0001-Fix-native-templates-directory-path.patch
Patch2:        0002-Use-python2-on-C8.patch
Requires:      %{?scl_prefix}ruby(rubygems)
Requires:      %{?scl_prefix}ruby(release)
Requires:      %{?scl_prefix}rubygem-nokogiri >= 1.4.0
Requires:      %{?scl_prefix}rubygem(sqlite3)
%{?scl:Requires:%scl_runtime}

BuildRequires: scl-utils
BuildRequires: scl-utils-build
%{?scl:BuildRequires: %{scl}-runtime}
BuildRequires: %{?scl_prefix}ruby
BuildRequires: %{?scl_prefix}rubygems-devel

%if 0%{?rhel} < 8
BuildRequires: python
Requires: python
%else
#BuildRequires: python36
#Requires: python36
BuildRequires: python2
Requires: python2
#BuildRequires: platform-python
%endif

%if 0%{?enable_tests}
BuildRequires: %{?scl_prefix}rubygem-rspec
%endif
BuildArch:     noarch
Provides:      %{?scl:%scl_prefix}rubygem(%{gem_name}) = %{version}

%description
A documentation formatting tool. Mizuho converts Asciidoc input files into
nicely outputted HTML, possibly one file per chapter. Multiple templates are
supported, so you can write your own.


%package doc
Summary:   Documentation for %{name}
Group:     Documentation
Requires:  %{name} = %{version}-%{release}
BuildArch: noarch

%description doc
Documentation for %{name}

%prep
%{?scl:scl enable %{scl} - << \EOF}
gem unpack %{SOURCE0}
%{?scl:EOF}

%setup -q -D -T -n  %{gem_name}-%{version}
%{?scl:scl enable %{scl} - << \EOF}
gem spec %{SOURCE0} -l --ruby > %{gem_name}.gemspec
%{?scl:EOF}

%patch1 -p 1

%if 0%{?rhel} >= 8
# On C8 ruby internally is referring to /usr/bin/python, make it python2
%patch2 -p 1
%endif

sed -i 's/NATIVELY_PACKAGED = .*/NATIVELY_PACKAGED = true/' lib/mizuho.rb
sed -i "s/__REPLACE_WITH_RUBY_VERSION__/%{ruby_version}/" lib/mizuho.rb

# Fixup rpmlint failures
echo "#toc.html" >> templates/toc.html

%build
%{?scl:scl enable %{scl} - << \EOF}
gem build %{gem_name}.gemspec
gem install \
        -V \
        --local \
        --install-dir .%{gem_dir} \
        --bindir .%{_bindir} \
        --force \
        --backtrace ./%{gem_name}-%{version}.gem
%{?scl:EOF}

%install
%global gemsbase opt/cpanel/ea-ruby27/root/usr/share/ruby/gems/ruby-%{ruby_version}
%global gemsusr opt/cpanel/ea-ruby27/root/usr
%global gemsmri %{gemsusr}/share/gems/gems/mizuho-%{version}
%global gemsdoc %{gemsusr}/share/gems/doc/mizuho-%{version}

%global gemsdir  %{gemsbase}/gems
%global mizbase  %{gemsdir}/mizuho-%{version}
%global mizdocs  %{gemsbase}/doc/mizuho-%{version}

%if 0%{?rhel} >= 8
find . -name "*.py" -print | xargs sed -i '1s:^#!/usr/bin/env python$:#!/usr/bin/env python2:'
%endif

mkdir -p %{buildroot}/%{_bindir}
mkdir -p %{buildroot}/%{mizbase}
mkdir -p %{buildroot}/%{mizdocs}
mkdir -p %{buildroot}/%{gemsbase}/specifications
mkdir -p %{buildroot}/%{gemsbase}/doc/mizuho-%{version}
mkdir -p %{buildroot}/%{gemsusr}/share/gems/specifications
mkdir -p %{buildroot}/%{gemsmri}

cp -ar %{gemsmri}/* %{buildroot}/%{mizbase}
cp -ar %{gemsmri}/* %{buildroot}/%{gemsmri}
cp -a  %{gemsusr}/bin/* %{buildroot}%{_bindir}
cp -a  %{gemsdoc}/* %{buildroot}/%{gemsbase}/doc/mizuho-%{version}
cp -a  %{gemsusr}/share/gems/specifications/mizuho-%{version}.gemspec %{buildroot}/%{gemsbase}/specifications/%{gem_name}-%{version}.gemspec
cp -a  %{gemsusr}/share/gems/specifications/mizuho-%{version}.gemspec %{buildroot}/%{gemsusr}/share/gems/specifications/%{gem_name}-%{version}.gemspec

find %{buildroot}/%{_bindir} -type f | xargs chmod a+x

# Remove build leftovers.
rm -rf %{buildroot}/%{mizbase}/{.rvmrc,.document,.require_paths,.gitignore,.travis.yml,.rspec,.gemtest,.yard*}

%check
%if 0%{?enable_tests}
pushd %{buildroot}/%{gemmri}
ruby -Ilib -S rspec -f s -c test/*_spec.rb
popd
%endif

%files
%dir /%{mizbase}
%doc /%{mizbase}/LICENSE.txt
%{_bindir}/mizuho
%{_bindir}/mizuho-asciidoc
/%{gemsbase}/specifications/%{gem_name}-%{version}.gemspec
%exclude /%{mizbase}/README.markdown
%exclude /%{mizbase}/Rakefile
%exclude /%{mizbase}/test/*
/%{mizbase}/asciidoc/BUGS
/%{mizbase}/asciidoc/BUGS.txt
/%{mizbase}/asciidoc/CHANGELOG
/%{mizbase}/asciidoc/CHANGELOG.txt
/%{mizbase}/asciidoc/COPYING
/%{mizbase}/asciidoc/COPYRIGHT
/%{mizbase}/asciidoc/INSTALL
/%{mizbase}/asciidoc/INSTALL.txt
/%{mizbase}/asciidoc/MANIFEST
/%{mizbase}/asciidoc/Makefile.in
/%{mizbase}/asciidoc/README
/%{mizbase}/asciidoc/README.txt
/%{mizbase}/asciidoc/a2x.py
/%{mizbase}/asciidoc/a2x.pyc
/%{mizbase}/asciidoc/a2x.pyo
/%{mizbase}/asciidoc/asciidoc.conf
/%{mizbase}/asciidoc/asciidoc.py
/%{mizbase}/asciidoc/asciidoc.pyc
/%{mizbase}/asciidoc/asciidoc.pyo
/%{mizbase}/asciidoc/asciidocapi.py
/%{mizbase}/asciidoc/asciidocapi.pyc
/%{mizbase}/asciidoc/asciidocapi.pyo
/%{mizbase}/asciidoc/common.aap
/%{mizbase}/asciidoc/configure
/%{mizbase}/asciidoc/configure.ac
/%{mizbase}/asciidoc/dblatex/asciidoc-dblatex.sty
/%{mizbase}/asciidoc/dblatex/asciidoc-dblatex.xsl
/%{mizbase}/asciidoc/dblatex/dblatex-readme.txt
/%{mizbase}/asciidoc/docbook-xsl/asciidoc-docbook-xsl.txt
/%{mizbase}/asciidoc/docbook-xsl/chunked.xsl
/%{mizbase}/asciidoc/docbook-xsl/common.xsl
/%{mizbase}/asciidoc/docbook-xsl/epub.xsl
/%{mizbase}/asciidoc/docbook-xsl/fo.xsl
/%{mizbase}/asciidoc/docbook-xsl/htmlhelp.xsl
/%{mizbase}/asciidoc/docbook-xsl/manpage.xsl
/%{mizbase}/asciidoc/docbook-xsl/text.xsl
/%{mizbase}/asciidoc/docbook-xsl/xhtml.xsl
/%{mizbase}/asciidoc/docbook45.conf
/%{mizbase}/asciidoc/examples/website/ASCIIMathML.js
/%{mizbase}/asciidoc/examples/website/CHANGELOG.txt
/%{mizbase}/asciidoc/examples/website/INSTALL.txt
/%{mizbase}/asciidoc/examples/website/LaTeXMathML.js
/%{mizbase}/asciidoc/examples/website/README-website.txt
/%{mizbase}/asciidoc/examples/website/README.txt
/%{mizbase}/asciidoc/examples/website/a2x.1.txt
/%{mizbase}/asciidoc/examples/website/asciidoc-docbook-xsl.txt
/%{mizbase}/asciidoc/examples/website/asciidoc-graphviz-sample.txt
/%{mizbase}/asciidoc/examples/website/asciidoc.css
/%{mizbase}/asciidoc/examples/website/asciidoc.js
/%{mizbase}/asciidoc/examples/website/asciidocapi.txt
/%{mizbase}/asciidoc/examples/website/asciimathml.txt
/%{mizbase}/asciidoc/examples/website/build-website.sh
/%{mizbase}/asciidoc/examples/website/customers.csv
/%{mizbase}/asciidoc/examples/website/epub-notes.txt
/%{mizbase}/asciidoc/examples/website/faq.txt
/%{mizbase}/asciidoc/examples/website/index.txt
/%{mizbase}/asciidoc/examples/website/latex-backend.txt
/%{mizbase}/asciidoc/examples/website/latex-bugs.txt
/%{mizbase}/asciidoc/examples/website/latex-filter.txt
/%{mizbase}/asciidoc/examples/website/latexmathml.txt
/%{mizbase}/asciidoc/examples/website/layout1.conf
/%{mizbase}/asciidoc/examples/website/layout1.css
/%{mizbase}/asciidoc/examples/website/layout2.conf
/%{mizbase}/asciidoc/examples/website/layout2.css
/%{mizbase}/asciidoc/examples/website/main.aap
/%{mizbase}/asciidoc/examples/website/manpage.txt
/%{mizbase}/asciidoc/examples/website/music-filter.txt
/%{mizbase}/asciidoc/examples/website/newlists.txt
/%{mizbase}/asciidoc/examples/website/newtables.txt
/%{mizbase}/asciidoc/examples/website/plugins.txt
/%{mizbase}/asciidoc/examples/website/publishing-ebooks-with-asciidoc.txt
/%{mizbase}/asciidoc/examples/website/slidy-example.txt
/%{mizbase}/asciidoc/examples/website/slidy.txt
/%{mizbase}/asciidoc/examples/website/source-highlight-filter.txt
/%{mizbase}/asciidoc/examples/website/support.txt
/%{mizbase}/asciidoc/examples/website/testasciidoc.txt
/%{mizbase}/asciidoc/examples/website/userguide.txt
/%{mizbase}/asciidoc/examples/website/version83.txt
/%{mizbase}/asciidoc/examples/website/xhtml11-quirks.css
/%{mizbase}/asciidoc/filters/code/code-filter-readme.txt
/%{mizbase}/asciidoc/filters/code/code-filter-test.txt
/%{mizbase}/asciidoc/filters/code/code-filter.conf
/%{mizbase}/asciidoc/filters/code/code-filter.py
/%{mizbase}/asciidoc/filters/code/code-filter.pyc
/%{mizbase}/asciidoc/filters/code/code-filter.pyo
/%{mizbase}/asciidoc/filters/graphviz/asciidoc-graphviz-sample.txt
/%{mizbase}/asciidoc/filters/graphviz/graphviz-filter.conf
/%{mizbase}/asciidoc/filters/graphviz/graphviz2png.py
/%{mizbase}/asciidoc/filters/graphviz/graphviz2png.pyc
/%{mizbase}/asciidoc/filters/graphviz/graphviz2png.pyo
/%{mizbase}/asciidoc/filters/latex/latex-filter.conf
/%{mizbase}/asciidoc/filters/latex/latex2png.py
/%{mizbase}/asciidoc/filters/latex/latex2png.pyc
/%{mizbase}/asciidoc/filters/latex/latex2png.pyo
/%{mizbase}/asciidoc/filters/music/music-filter-test.txt
/%{mizbase}/asciidoc/filters/music/music-filter.conf
/%{mizbase}/asciidoc/filters/music/music2png.py
/%{mizbase}/asciidoc/filters/music/music2png.pyc
/%{mizbase}/asciidoc/filters/music/music2png.pyo
/%{mizbase}/asciidoc/filters/source/source-highlight-filter-test.txt
/%{mizbase}/asciidoc/filters/source/source-highlight-filter.conf
/%{mizbase}/asciidoc/help.conf
/%{mizbase}/asciidoc/html4.conf
/%{mizbase}/asciidoc/html5.conf
/%{mizbase}/asciidoc/images/highlighter.png
/%{mizbase}/asciidoc/images/icons/README
/%{mizbase}/asciidoc/images/icons/callouts/1.png
/%{mizbase}/asciidoc/images/icons/callouts/10.png
/%{mizbase}/asciidoc/images/icons/callouts/11.png
/%{mizbase}/asciidoc/images/icons/callouts/12.png
/%{mizbase}/asciidoc/images/icons/callouts/13.png
/%{mizbase}/asciidoc/images/icons/callouts/14.png
/%{mizbase}/asciidoc/images/icons/callouts/15.png
/%{mizbase}/asciidoc/images/icons/callouts/2.png
/%{mizbase}/asciidoc/images/icons/callouts/3.png
/%{mizbase}/asciidoc/images/icons/callouts/4.png
/%{mizbase}/asciidoc/images/icons/callouts/5.png
/%{mizbase}/asciidoc/images/icons/callouts/6.png
/%{mizbase}/asciidoc/images/icons/callouts/7.png
/%{mizbase}/asciidoc/images/icons/callouts/8.png
/%{mizbase}/asciidoc/images/icons/callouts/9.png
/%{mizbase}/asciidoc/images/icons/caution.png
/%{mizbase}/asciidoc/images/icons/example.png
/%{mizbase}/asciidoc/images/icons/home.png
/%{mizbase}/asciidoc/images/icons/important.png
/%{mizbase}/asciidoc/images/icons/next.png
/%{mizbase}/asciidoc/images/icons/note.png
/%{mizbase}/asciidoc/images/icons/prev.png
/%{mizbase}/asciidoc/images/icons/tip.png
/%{mizbase}/asciidoc/images/icons/up.png
/%{mizbase}/asciidoc/images/icons/warning.png
/%{mizbase}/asciidoc/images/smallnew.png
/%{mizbase}/asciidoc/images/tiger.png
/%{mizbase}/asciidoc/install-sh
/%{mizbase}/asciidoc/javascripts/ASCIIMathML.js
/%{mizbase}/asciidoc/javascripts/LaTeXMathML.js
/%{mizbase}/asciidoc/javascripts/asciidoc.js
/%{mizbase}/asciidoc/javascripts/slidy.js
/%{mizbase}/asciidoc/javascripts/toc.js
/%{mizbase}/asciidoc/lang-de.conf
/%{mizbase}/asciidoc/lang-en.conf
/%{mizbase}/asciidoc/lang-es.conf
/%{mizbase}/asciidoc/lang-fr.conf
/%{mizbase}/asciidoc/lang-hu.conf
/%{mizbase}/asciidoc/lang-it.conf
/%{mizbase}/asciidoc/lang-nl.conf
/%{mizbase}/asciidoc/lang-pt-BR.conf
/%{mizbase}/asciidoc/lang-ru.conf
/%{mizbase}/asciidoc/lang-uk.conf
/%{mizbase}/asciidoc/latex.conf
/%{mizbase}/asciidoc/main.aap
/%{mizbase}/asciidoc/slidy.conf
/%{mizbase}/asciidoc/stylesheets/asciidoc.css
/%{mizbase}/asciidoc/stylesheets/docbook-xsl.css
/%{mizbase}/asciidoc/stylesheets/pygments.css
/%{mizbase}/asciidoc/stylesheets/slidy.css
/%{mizbase}/asciidoc/stylesheets/toc2.css
/%{mizbase}/asciidoc/stylesheets/xhtml11-quirks.css
/%{mizbase}/asciidoc/tests/asciidocapi.py
/%{mizbase}/asciidoc/tests/asciidocapi.pyc
/%{mizbase}/asciidoc/tests/asciidocapi.pyo
/%{mizbase}/asciidoc/tests/data/deprecated-quotes.txt
/%{mizbase}/asciidoc/tests/data/filters-test.txt
/%{mizbase}/asciidoc/tests/data/lang-de-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-de-test.txt
/%{mizbase}/asciidoc/tests/data/lang-en-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-en-test.txt
/%{mizbase}/asciidoc/tests/data/lang-es-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-es-test.txt
/%{mizbase}/asciidoc/tests/data/lang-fr-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-fr-test.txt
/%{mizbase}/asciidoc/tests/data/lang-hu-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-hu-test.txt
/%{mizbase}/asciidoc/tests/data/lang-it-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-it-test.txt
/%{mizbase}/asciidoc/tests/data/lang-nl-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-nl-test.txt
/%{mizbase}/asciidoc/tests/data/lang-pt-BR-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-pt-BR-test.txt
/%{mizbase}/asciidoc/tests/data/lang-ru-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-ru-test.txt
/%{mizbase}/asciidoc/tests/data/lang-uk-man-test.txt
/%{mizbase}/asciidoc/tests/data/lang-uk-test.txt
/%{mizbase}/asciidoc/tests/data/oldtables.txt
/%{mizbase}/asciidoc/tests/data/rcs-id-marker-test.txt
/%{mizbase}/asciidoc/tests/data/testcases.conf
/%{mizbase}/asciidoc/tests/data/testcases.txt
/%{mizbase}/asciidoc/tests/data/utf8-bom-test.txt
/%{mizbase}/asciidoc/tests/data/utf8-examples.txt
/%{mizbase}/asciidoc/tests/testasciidoc.conf
/%{mizbase}/asciidoc/tests/testasciidoc.py
/%{mizbase}/asciidoc/tests/testasciidoc.pyc
/%{mizbase}/asciidoc/tests/testasciidoc.pyo
/%{mizbase}/asciidoc/text.conf
/%{mizbase}/asciidoc/themes/flask/flask.css
/%{mizbase}/asciidoc/themes/volnitsky/volnitsky.css
/%{mizbase}/asciidoc/vim/ftdetect/asciidoc_filetype.vim
/%{mizbase}/asciidoc/vim/syntax/asciidoc.vim
/%{mizbase}/asciidoc/wordpress.conf
/%{mizbase}/asciidoc/xhtml11-quirks.conf
/%{mizbase}/asciidoc/xhtml11.conf
/%{mizbase}/bin/mizuho
/%{mizbase}/bin/mizuho-asciidoc
/%{mizbase}/debian.template/changelog
/%{mizbase}/debian.template/compat
/%{mizbase}/debian.template/control.template
/%{mizbase}/debian.template/copyright
/%{mizbase}/debian.template/mizuho.install.template
/%{mizbase}/debian.template/ruby-interpreter
/%{mizbase}/debian.template/rules.template
/%{mizbase}/debian.template/source/format
/%{mizbase}/lib/mizuho.rb
/%{mizbase}/lib/mizuho/fuzzystringmatch.rb
/%{mizbase}/lib/mizuho/generator.rb
/%{mizbase}/lib/mizuho/id_map.rb
/%{mizbase}/lib/mizuho/packaging.rb
/%{mizbase}/lib/mizuho/source_highlight.rb
/%{mizbase}/lib/mizuho/utils.rb
/%{mizbase}/mizuho.gemspec
/%{mizbase}/rpm/get_distro_id.py
/%{mizbase}/rpm/get_distro_id.pyc
/%{mizbase}/rpm/get_distro_id.pyo
/%{mizbase}/rpm/rubygem-mizuho.spec.template
/%{mizbase}/source-highlight/ada.lang
/%{mizbase}/source-highlight/bib.lang
/%{mizbase}/source-highlight/bison.lang
/%{mizbase}/source-highlight/c.lang
/%{mizbase}/source-highlight/c_comment.lang
/%{mizbase}/source-highlight/c_string.lang
/%{mizbase}/source-highlight/caml.lang
/%{mizbase}/source-highlight/changelog.lang
/%{mizbase}/source-highlight/clike_vardeclaration.lang
/%{mizbase}/source-highlight/cpp.lang
/%{mizbase}/source-highlight/csharp.lang
/%{mizbase}/source-highlight/css.lang
/%{mizbase}/source-highlight/css_common.outlang
/%{mizbase}/source-highlight/darwin/source-highlight
/%{mizbase}/source-highlight/default.css
/%{mizbase}/source-highlight/default.lang
/%{mizbase}/source-highlight/default.style
/%{mizbase}/source-highlight/desktop.lang
/%{mizbase}/source-highlight/diff.lang
/%{mizbase}/source-highlight/docbook.outlang
/%{mizbase}/source-highlight/esc.outlang
/%{mizbase}/source-highlight/esc.style
/%{mizbase}/source-highlight/extreme_comment.lang
/%{mizbase}/source-highlight/extreme_comment2.lang
/%{mizbase}/source-highlight/extreme_comment3.lang
/%{mizbase}/source-highlight/fixed-fortran.lang
/%{mizbase}/source-highlight/flex.lang
/%{mizbase}/source-highlight/fortran.lang
/%{mizbase}/source-highlight/function.lang
/%{mizbase}/source-highlight/glsl.lang
/%{mizbase}/source-highlight/haxe.lang
/%{mizbase}/source-highlight/html.lang
/%{mizbase}/source-highlight/html.outlang
/%{mizbase}/source-highlight/html_common.outlang
/%{mizbase}/source-highlight/html_notfixed.outlang
/%{mizbase}/source-highlight/html_ref.outlang
/%{mizbase}/source-highlight/htmlcss.outlang
/%{mizbase}/source-highlight/htmltable.outlang
/%{mizbase}/source-highlight/htmltablelinenum.outlang
/%{mizbase}/source-highlight/java.lang
/%{mizbase}/source-highlight/javadoc.outlang
/%{mizbase}/source-highlight/javascript.lang
/%{mizbase}/source-highlight/key_string.lang
/%{mizbase}/source-highlight/lang.map
/%{mizbase}/source-highlight/langdef.lang
/%{mizbase}/source-highlight/latex.lang
/%{mizbase}/source-highlight/latex.outlang
/%{mizbase}/source-highlight/latexcolor.outlang
/%{mizbase}/source-highlight/ldap.lang
/%{mizbase}/source-highlight/log.lang
/%{mizbase}/source-highlight/logtalk.lang
/%{mizbase}/source-highlight/lsm.lang
/%{mizbase}/source-highlight/lua.lang
/%{mizbase}/source-highlight/m4.lang
/%{mizbase}/source-highlight/makefile.lang
/%{mizbase}/source-highlight/nohilite.lang
/%{mizbase}/source-highlight/number.lang
/%{mizbase}/source-highlight/outlang.lang
/%{mizbase}/source-highlight/outlang.map
/%{mizbase}/source-highlight/pascal.lang
/%{mizbase}/source-highlight/perl.lang
/%{mizbase}/source-highlight/php.lang
/%{mizbase}/source-highlight/postscript.lang
/%{mizbase}/source-highlight/prolog.lang
/%{mizbase}/source-highlight/properties.lang
/%{mizbase}/source-highlight/python.lang
/%{mizbase}/source-highlight/ruby.lang
/%{mizbase}/source-highlight/scala.lang
/%{mizbase}/source-highlight/script_comment.lang
/%{mizbase}/source-highlight/sh.lang
/%{mizbase}/source-highlight/slang.lang
/%{mizbase}/source-highlight/sml.lang
/%{mizbase}/source-highlight/source-highlight
/%{mizbase}/source-highlight/spec.lang
/%{mizbase}/source-highlight/sql.lang
/%{mizbase}/source-highlight/style.defaults
/%{mizbase}/source-highlight/style.lang
/%{mizbase}/source-highlight/style2.style
/%{mizbase}/source-highlight/style3.style
/%{mizbase}/source-highlight/symbols.lang
/%{mizbase}/source-highlight/tcl.lang
/%{mizbase}/source-highlight/texinfo.outlang
/%{mizbase}/source-highlight/texinfo.style
/%{mizbase}/source-highlight/url.lang
/%{mizbase}/source-highlight/xhtml.outlang
/%{mizbase}/source-highlight/xhtml_common.outlang
/%{mizbase}/source-highlight/xhtml_notfixed.outlang
/%{mizbase}/source-highlight/xhtmlcss.outlang
/%{mizbase}/source-highlight/xhtmltable.outlang
/%{mizbase}/source-highlight/xml.lang
/%{mizbase}/source-highlight/xorg.lang
/%{mizbase}/templates/arrow-up.png
/%{mizbase}/templates/balloon.png
/%{mizbase}/templates/balloon.svg
/%{mizbase}/templates/jquery-1.6.1.min.js
/%{mizbase}/templates/jquery-1.7.1.min.js
/%{mizbase}/templates/jquery.hashchange-1.0.0.js
/%{mizbase}/templates/juvia.js
/%{mizbase}/templates/mizuho.css
/%{mizbase}/templates/mizuho.js
/%{mizbase}/templates/toc.html
/%{mizbase}/templates/topbar.css
/%{mizbase}/templates/topbar.html
/%{mizbase}/templates/topbar.js
/opt/cpanel/ea-ruby27/root/usr/share/gems/specifications/mizuho-%{version}.gemspec
/%{gemsmri}

%files doc
%doc /%{mizbase}/README.markdown
%doc /%{gemsbase}/doc/mizuho-%{version}
/%{mizbase}/Rakefile
/%{mizbase}/test/generator_spec.rb
/%{mizbase}/test/id_map_spec.rb
/%{mizbase}/test/parser_spec.rb
/%{mizbase}/test/spec_helper.rb
/%{mizbase}/asciidoc/doc/a2x.1
/%{mizbase}/asciidoc/doc/a2x.1.txt
/%{mizbase}/asciidoc/doc/article-docinfo.xml
/%{mizbase}/asciidoc/doc/article.pdf
/%{mizbase}/asciidoc/doc/article.txt
/%{mizbase}/asciidoc/doc/asciidoc.1
/%{mizbase}/asciidoc/doc/asciidoc.1.txt
/%{mizbase}/asciidoc/doc/asciidoc.conf
/%{mizbase}/asciidoc/doc/asciidoc.dict
/%{mizbase}/asciidoc/doc/asciidoc.txt
/%{mizbase}/asciidoc/doc/asciidocapi.txt
/%{mizbase}/asciidoc/doc/asciimathml.txt
/%{mizbase}/asciidoc/doc/book-multi.txt
/%{mizbase}/asciidoc/doc/book.epub
/%{mizbase}/asciidoc/doc/book.txt
/%{mizbase}/asciidoc/doc/customers.csv
/%{mizbase}/asciidoc/doc/epub-notes.txt
/%{mizbase}/asciidoc/doc/faq.txt
/%{mizbase}/asciidoc/doc/latex-backend.txt
/%{mizbase}/asciidoc/doc/latex-bugs.txt
/%{mizbase}/asciidoc/doc/latex-filter.pdf
/%{mizbase}/asciidoc/doc/latex-filter.txt
/%{mizbase}/asciidoc/doc/latexmath.txt
/%{mizbase}/asciidoc/doc/latexmathml.txt
/%{mizbase}/asciidoc/doc/main.aap
/%{mizbase}/asciidoc/doc/music-filter.pdf
/%{mizbase}/asciidoc/doc/music-filter.txt
/%{mizbase}/asciidoc/doc/publishing-ebooks-with-asciidoc.txt
/%{mizbase}/asciidoc/doc/slidy-example.txt
/%{mizbase}/asciidoc/doc/slidy.txt
/%{mizbase}/asciidoc/doc/source-highlight-filter.pdf
/%{mizbase}/asciidoc/doc/source-highlight-filter.txt
/%{mizbase}/asciidoc/doc/testasciidoc.txt

%changelog
* Tue Dec 28 2021 Dan Muey <dan@cpanel.net> - 0.9.20-6
- ZC-9589: Update DISABLE_BUILD to match OBS

* Wed Nov 24 2021 Travis Holloway <t.holloway@cpanel.net> - 0.9.20-5
- EA-10301: ea-ruby27 was updated from v2.7.4 to v2.7.5

* Thu Jul 29 2021 Travis Holloway <t.holloway@cpanel.net> - 0.9.20-4
- EA-10007: ea-ruby27 was updated from v2.7.3 to v2.7.4

* Tue Jun 29 2021 Julian Brown <julian.brown@cpanel.net> - 0.9.20-3
- ZC-9033: provide reliable way to get the ruby_version

* Wed Oct 21 2020 Daniel Muey <dan@cpanel.net> - 0.9.20-2
- ZC-7497: do conditional inside %check

* Wed Sep 09 2020 Julian Brown <julian.brown@cpanel.net> - 0.9.20-1
- ZC-7512 - Initial package on Ruby2.7

