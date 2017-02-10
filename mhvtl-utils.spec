%{!?kversion:
    %{?kdir:%define kversion %{expand:%%(
        make -sC "%{kdir}" kernelversion | grep -v ^make)}
    }
    %{!?kdir:
        %define kversion %{expand:%%(
            if rpm --quiet -q kernel-headers; then
                rpm -q --qf '%%%%{BUILDTIME} %%%%{version}-%%%%{release}.%%%%{arch}\\n' \\
                    kernel-headers | sort | tail -n1 | { read a b; echo $b; };
            else
                uname -r;
            fi
        )}
    }
}
%{echo:kversion=%{kversion}}

%define krpmver %{expand:%%(
            echo -n "%%{kversion}" | sed -e 's/\\.[^.]\\{1,\\}$//'
        )}


Summary: Virtual tape library. kernel pseudo HBA driver + userspace daemons
Name: mhvtl
Version: 1.5
Release: 5%{?dist}
License: GPL
Group: System/Kernel
URL: http://sites.google.com/site/linuxvtl2/

Source: mhvtl-2016-09-26.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-build-%(%{__id_u} -n)

BuildRequires:   zlib-devel, redhat-rpm-config, kernel-devel
Requires:        glibc, zlib, initscripts >= 8.36, gawk, util-linux, mhvtl-kmod
Requires(pre):   glibc-common, shadow-utils
Requires(post):  chkconfig
Requires(preun): chkconfig

Provides: mhvtl = %{version}-%{release}

%description
A Virtual tape library and tape drives:

Used to emulate hardware robot & tape drives:

VTL consists of a pseudo HBA kernel driver and user-space daemons which
function as the SCSI target.

Communication between the kernel module and the daemons is achieved
via /dev/mhvtl? device nodes.

The kernel module is based on the scsi_debug driver.
The SSC/SMC target daemons have been written from scratch.

%package kmod
Summary:  Virtual tape library kernel module
Requires: kmod, kernel = %{krpmver}, util-linux

%description kmod
Virtual tape library kernel module

%prep
%setup -n mhvtl-%{version}

%build
%{__make} RPM_OPT_FLAGS="%{optflags}" VERSION="%{version}.%{release}" usr
%{__make} RPM_OPT_FLAGS="%{optflags}" VERSION="%{version}.%{release}" INITD="%{_initrddir}" etc
%{__make} RPM_OPT_FLAGS="%{optflags}" VERSION="%{version}.%{release}" scripts
%{__make} -C kernel

%install
%{__rm} -rf %{buildroot}
%{__make} install DESTDIR="%{buildroot}" INITD="%{_initrddir}" LIBDIR="%{_libdir}"
KINST="%{buildroot}/lib/modules/%{kversion}/kernel/drivers/scsi"
%{__mkdir} -p "$KINST"
%{__install} -m 644 kernel/mhvtl.ko "$KINST/"

%clean
%{__rm} -rf %{buildroot}

%pre
if ! getent group vtl >/dev/null; then
	groupadd -r vtl
fi
if ! getent passwd vtl >/dev/null; then
	useradd -r -g vtl -c "VTL daemon" -d /opt/mhvtl -s /sbin/nologin vtl
fi

%post
ldconfig
chkconfig --add mhvtl
chkconfig mhvtl off
grep -qs systemd /proc/1/comm && systemctl daemon-reload
exit 0

%preun
if (( $1 == 0 )); then
	cd "%{_initrddir}"
	./mhvtl stop >/dev/null 2>&1
	chkconfig --del mhvtl
	grep -qs systemd /proc/1/comm && systemctl daemon-reload
fi
exit 0

%postun
ldconfig
exit 0

%files
%defattr(644,root,root,755)
%doc INSTALL README etc/library_contents.sample
%doc %{_mandir}/man1/build_library_config.1*
%doc %{_mandir}/man1/mhvtl.1*
%doc %{_mandir}/man1/mktape.1*
%doc %{_mandir}/man1/edit_tape.1*
%doc %{_mandir}/man1/vtlcmd.1*
%doc %{_mandir}/man1/vtllibrary.1*
%doc %{_mandir}/man1/vtltape.1*
%doc %{_mandir}/man1/make_vtl_media.1*
%doc %{_mandir}/man5/device.conf.5*
%doc %{_mandir}/man5/mhvtl.conf.5*
%doc %{_mandir}/man5/library_contents.5*
%attr(754,root,root) %{_initrddir}/mhvtl
%attr(755,root,root) %{_bindir}/vtlcmd
%attr(755,root,root) %{_bindir}/mktape
%attr(755,root,root) %{_bindir}/edit_tape
%attr(755,root,root) %{_bindir}/dump_tape
%attr(755,root,root) %{_bindir}/tapeexerciser
%attr(755,root,root) %{_bindir}/build_library_config
%attr(755,root,root) %{_bindir}/make_vtl_media
%attr(755,root,root) %{_bindir}/update_device.conf
%{_libdir}/libvtlscsi.so
%{_libdir}/libvtlcart.so
%attr(755,root,root) %{_bindir}/vtltape
%attr(755,root,root) %{_bindir}/vtllibrary
%dir %attr(770,vtl,vtl) /opt/mhvtl

%post kmod
depmod -a %{kversion}
exit 0

%preun kmod
if (( $1 == 0 )); then
	cd "%{_initrddir}"
	./mhvtl shutdown >/dev/null 2>&1
	rmmod mhvtl >/dev/null 2>&1
	Q_EXISTS=`ipcs -q | awk '/4d61726b/ {print $2}'`
	[ -n "$Q_EXISTS" ] && ipcrm -q $Q_EXISTS
fi
exit 0

%postun kmod
depmod -a %{kversion}
exit 0

%files kmod
%defattr(644,root,root,755)
/lib/modules/%{kversion}/kernel/drivers/scsi/mhvtl.ko
