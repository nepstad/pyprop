
SUBDIRS = 1d cartesian spherical combined

all clean pyclean: $(SUBDIRS)
	for subdir in $(SUBDIRS); do (cd $${subdir}; $(MAKE) $@); done 
