# Contributing to schemachange

## Reporting issues

When reporting issues please include as much detail as possible about your
operating environment, schemachange version and python version. Whenever possible, please
also include a brief, self-contained code example that demonstrates the problem.

We have included [issue templates for reporting bugs, requesting features and seeking clarifications.](https://github.com/Snowflake-Labs/schemachange/issues/new/choose)
Choose the appropriate issue template to contribute to the repository.

## Contributing code

Thanks for your interest in contributing code to schemachange!

+ If this is your first time contributing to a project on GitHub, please read through our [guide to contributing to schemachange](guide-to-contributing-to-schemachange).
+ There are many online tutorials to help you [learn git](https://try.github.io/). For discussions of specific git workflows, see these discussions on [linux git workflow](https://www.mail-archive.com/dri-devel@lists.sourceforge.net/msg39091.html), and [ipython git workflow](https://mail.python.org/pipermail/ipython-dev/2010-October/005632.html).

### Guide to contributing to schemachange

1. If you are a first-time contributor
    + Go to [Snowflake-Labs/Schemachange](https://github.com/Snowflake-Labs/schemachange) and click the "fork" button to create your own copy of the project.
    + [Clone](https://github.com/git-guides/git-clone) the project to your local computer

    ```shell
    git clone https://github.com/your-username/schemachange.git

    ```

    + Change the directory

    ```shell
    cd schemachange

    ```
    + Add upstream repository:

    ```shell
    git remote add upstream https://github.com/Snowflake-Labs/schemachange

    ```

    + Now, `git remote -v` will show two [remote](https://github.com/git-guides/git-remote) repositories named:
      + `upstream`, which refers to the `schemachange` repository
      + `origin`, which refers to your personal fork
    + [Pull](https://github.com/git-guides/git-pull) the latest changes from upstream, including tags:

    ```shell
    git checkout main
    git pull upstream main --tags

    ```

3. Develop your contribution
    + Create a branch for the features you want to work on. Since the branch name will appear in the merge message, use a sensible name such as 'update-build-library-dependencies':

    ```shell
    git checkout -b update-build-library-dependencies
    ```

    + Commit locally as you progress ( [git add](https://github.com/git-guides/git-add) and [git commit](https://github.com/git-guides/git-commit) ). Use a properly formatted commit message. Be sure to document any changed behavior.
4. To submit your contribution
    + [Push](https://github.com/git-guides/git-push) your changes back to your fork on GitHub

    ```shell
    git push origin update-build-library-dependencies

    ```

    + Go to GitHub. The new branch will show up with a green [Pull Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#initiating-the-pull-request) button. Make sure the title and message are clear, concise and self explanatory. Then click the button to submit it.
