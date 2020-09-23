# Defining the package namespace
%global ns_name ea
%global ns_dir /opt/cpanel
%global pkg ruby27
%global gem_name mizuho

# NOTE: I need the version, is there a better way?
%global ruby_version 2.7.1

# Force Software Collections on
%global _scl_prefix %{ns_dir}
%global scl %{ns_name}-%{pkg}
# HACK: OBS Doesn't support macros in BuildRequires statements, so we have
#       to hard-code it here.
# https://en.opensuse.org/openSUSE:Specfile_guidelines#BuildRequires
%global scl_prefix %{scl}-
%{?scl:%scl_package rubygem-%{gem_name}}

# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4590 for more details
%define release_prefix 1

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

sed -i 's/NATIVELY_PACKAGED = .*/NATIVELY_PACKAGED = true/' lib/mizuho.rb

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

echo "FILELIST"
find . -type f -print

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

cp -ar %{gemsmri}/* %{buildroot}/%{mizbase}
cp -a  %{gemsusr}/bin/* %{buildroot}%{_bindir}
cp -a  %{gemsdoc}/* %{buildroot}/%{gemsbase}/doc/mizuho-%{version}
cp -a  %{gemsusr}/share/gems/specifications/mizuho-%{version}.gemspec %{buildroot}/%{gemsbase}/specifications/%{gem_name}-%{version}.gemspec

find %{buildroot}/%{_bindir} -type f | xargs chmod a+x

# Remove build leftovers.
rm -rf %{buildroot}/%{mizbase}/{.rvmrc,.document,.require_paths,.gitignore,.travis.yml,.rspec,.gemtest,.yard*}

%if 0%{?enable_tests}
%check
echo "CHECK: 001"
pushd %{buildroot}/%{gemmri}
ruby -Ilib -S rspec -f s -c test/*_spec.rb
popd
%endif

%files
%dir /%{mizbase}
%doc /%{mizbase}/LICENSE.txt
/%{mizbase}/*
/%{mizbase}/asciidoc/*
/%{mizbase}/asciidoc/dblatex/*
/%{mizbase}/asciidoc/doc/*
/%{mizbase}/asciidoc/docbook-xsl/*
/%{mizbase}/asciidoc/examples/website/*
/%{mizbase}/asciidoc/filters/code/*
/%{mizbase}/asciidoc/filters/graphviz/*
/%{mizbase}/asciidoc/filters/latex/*
/%{mizbase}/asciidoc/filters/music/*
/%{mizbase}/asciidoc/filters/source/*
/%{mizbase}/asciidoc/images/*
/%{mizbase}/asciidoc/images/icons/*
/%{mizbase}/asciidoc/images/icons/callouts/*
/%{mizbase}/asciidoc/javascripts/*
/%{mizbase}/asciidoc/stylesheets/*
/%{mizbase}/asciidoc/tests/*
/%{mizbase}/asciidoc/tests/data/*
/%{mizbase}/asciidoc/themes/flask/*
/%{mizbase}/asciidoc/themes/volnitsky/*
/%{mizbase}/asciidoc/vim/ftdetect/*
/%{mizbase}/asciidoc/vim/syntax/*
/%{mizbase}/bin/*
/%{mizbase}/debian.template/*
/%{mizbase}/lib/*
/%{mizbase}/lib/mizuho/*
/%{mizbase}/rpm/*
/%{mizbase}/source-highlight/*
/%{mizbase}/templates/*
%{_bindir}/mizuho
%{_bindir}/mizuho-asciidoc
/%{gemsbase}/specifications/%{gem_name}-%{version}.gemspec
%exclude /%{mizbase}/README.markdown
%exclude /%{mizbase}/Rakefile
%exclude /%{mizbase}/test/*

%files doc
%doc /%{mizbase}/README.markdown
%doc /%{gemsbase}/doc/mizuho-%{version}
/%{mizbase}/Rakefile
/%{mizbase}/test/*
/%{gemsbase}/doc/mizuho-%{version}/*
/%{gemsbase}/doc/mizuho-%{version}/*/*
/%{gemsbase}/doc/mizuho-%{version}/*/*/*

%changelog
* Wed Sep 09 2020 Julian Brown <julian.brown@cpanel.net> - 0.9.20-1
- ZC-7512 - Initial package on Ruby2.7

