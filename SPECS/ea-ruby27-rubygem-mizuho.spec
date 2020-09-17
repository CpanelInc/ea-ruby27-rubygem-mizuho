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
%global __python /usr/bin/python3
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
Patch2:        0002-CentOS-8-requires-Python3.patch
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
#%patch2 -p 1
%endif

sed -i 's/NATIVELY_PACKAGED = .*/NATIVELY_PACKAGED = true/' lib/mizuho.rb

# Fixup rpmlint failures
echo "#toc.html" >> templates/toc.html


%build
echo "python" %{__python3}

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
%global gemsusr opt/cpanel/ea-ruby27/root/usr
%global gemsmri %{gemsusr}/share/gems/gems/mizuho-%{version}
%global gemsdoc %{gemsusr}/share/gems/doc/mizuho-%{version}

%if 0%{?rhel} >= 8
find . -name "*.py" -print | xargs sed -i '1s:^#!/usr/bin/env python$:#!/usr/bin/env python2:' 
%endif

mkdir -p %{buildroot}/%{gemsmri}
mkdir -p %{buildroot}/%{gemsdoc}
mkdir -p %{buildroot}/%{gemsusr}/bin

cp -ar %{gemsmri}/* %{buildroot}/%{gemsmri}
cp -ar %{gemsdoc}/* %{buildroot}/%{gemsdoc}
cp -a   %{gemsusr}/bin/* %{buildroot}/%{gemsusr}/bin

find %{buildroot}/%{gemsusr}/bin -type f | xargs chmod a+x

# Remove build leftovers.
rm -rf %{buildroot}/%{gemsmri}/{.rvmrc,.document,.require_paths,.gitignore,.travis.yml,.rspec,.gemtest,.yard*}

%if 0%{?enable_tests}
%check
echo "CHECK: 001"
pushd %{buildroot}/%{gemmri}
ruby -Ilib -S rspec -f s -c test/*_spec.rb
popd
%endif

%files
%dir /%{gemsmri}
%doc /%{gemsmri}/LICENSE.txt
/%{gemsmri}/*
/%{gemsmri}/asciidoc/*
/%{gemsmri}/asciidoc/dblatex/*
/%{gemsmri}/asciidoc/doc/*
/%{gemsmri}/asciidoc/docbook-xsl/*
/%{gemsmri}/asciidoc/examples/website/*
/%{gemsmri}/asciidoc/filters/code/*
/%{gemsmri}/asciidoc/filters/graphviz/*
/%{gemsmri}/asciidoc/filters/latex/*
/%{gemsmri}/asciidoc/filters/music/*
/%{gemsmri}/asciidoc/filters/source/*
/%{gemsmri}/asciidoc/images/*
/%{gemsmri}/asciidoc/images/icons/*
/%{gemsmri}/asciidoc/images/icons/callouts/*
/%{gemsmri}/asciidoc/javascripts/*
/%{gemsmri}/asciidoc/stylesheets/*
/%{gemsmri}/asciidoc/tests/*
/%{gemsmri}/asciidoc/tests/data/*
/%{gemsmri}/asciidoc/themes/flask/*
/%{gemsmri}/asciidoc/themes/volnitsky/*
/%{gemsmri}/asciidoc/vim/ftdetect/*
/%{gemsmri}/asciidoc/vim/syntax/*
/%{gemsmri}/bin/*
/%{gemsmri}/debian.template/*
/%{gemsmri}/lib/*
/%{gemsmri}/lib/mizuho/*
/%{gemsmri}/rpm/*
/%{gemsmri}/source-highlight/*
/%{gemsmri}/templates/*
%{_bindir}/mizuho
%{_bindir}/mizuho-asciidoc
%exclude /%{gemsmri}/README.markdown
%exclude /%{gemsmri}/Rakefile
%exclude /%{gemsmri}/test/*

%files doc
%doc /%{gemsmri}/README.markdown
%doc /%{gemsdoc}
/%{gemsmri}/Rakefile
/%{gemsmri}/test/*

%changelog
* Wed Sep 09 2020 Julian Brown <julian.brown@cpanel.net> - 0.9.20-1
- ZC-7512 - Initial package on Ruby2.7

