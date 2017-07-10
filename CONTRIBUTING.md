# Contributing to Icarus

Contributions to Icarus codebase from the community are very much welcome.

This document provides an overview of ways you could contribute to Icarus and
guidelines on how to prepare and submit your contribution.

# How you can contribute

You could contribute to Icarus with following:

 * *Bug fixes*: any bug fix is very much welcome

 * *Documentation improvement*: any improvement to the documentation is welcome too

 * *Changes to core functionalities of Icarus*:
   These are changes to parts of the codebase that can change the overall
   behavior of the simulator. These contributions are normally accepted as long
   as they do not break other functionalities and do not reduce performance or
   increase complexity, unless there are reasonable justifications for it.

 * *New pluggable components*:
   These pluggable components include cache replacement policies, caching
   strategies, workloads, topologies, cache placement algorithms and so on.
   Differently from changes to core functionalities, adding pluggable components
   do not affect the rest of the codebase.
   Implementations of new pluggable components are normally accepted if they
   implement mechanisms published in peer-reviewed publications or extensively
   documented and evaluated.

# Preparing and submitting your contribution

To contribute your code, please open a pull request on the `icarus-sim/icarus`
repository on Github. After you open a pull request, merging your contributions
will be discussed and you may be requested to make some amendments, for example
to fix issues or to ensure that the style of your contribution is consistent
with the rest of the codebase.

Here are some guidelines to follow while preparing your contribution:

 * Write code following the coding conventions specified in the PEP8 specifications.
   There are tools such as `pep8` and `flake8` that you can use to validate the
   compliance of your code.

 * Write clear Git commit messages, following Git convention.

 * Before opening a pull request, rebase your branch on top of the current Icarus
   master branch if changes were pushed to the master branch after you cloned it.

 * Ensure that your code does not break any other tests. You can run test cases
   by running `make test`. In addition, whenever you push a commit to
   Github, Travis-CI will automatically run all those test cases against various
   versions of Python and email you if tests fail.

 * Document all classes, methods and functions that you add using the Numpydoc
   format. You can look at the Icarus codebase for examples.

 * Unless your changes are trivial, please consider writing test cases for them.
