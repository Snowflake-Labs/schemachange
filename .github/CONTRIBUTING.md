# Contributing to schemachange

## Reporting issues

When reporting issues please include as much detail as possible about your
operating environment, schemachange version and python version. Whenever possible, please
also include a brief, self-contained code example that demonstrates the problem.

We have
included [issue templates](https://github.com/Snowflake-Labs/schemachange/issues/new/choose) for reporting bugs, requesting features and seeking clarifications. Choose the appropriate issue template to contribute to the repository.

## Contributing code

Thank you for your interest in contributing code to schemachange!

+ If this is your first time contributing to a project on GitHub, please continue reading through
  [our guide to contributing to schemachange](#guide-to-contributing-to-schemachange).
+ There are many online tutorials to help you [learn git](https://try.github.io/). For discussions of specific git
  workflows, see these discussions
  on [linux git workflow](https://www.mail-archive.com/dri-devel@lists.sourceforge.net/msg39091.html),
  and [ipython git workflow](https://mail.python.org/pipermail/ipython-dev/2010-October/005632.html).

### Guide to contributing to schemachange

1. If you are a first-time contributor
    + Go to [Snowflake-Labs/Schemachange](https://github.com/Snowflake-Labs/schemachange) and click the "fork" button to
      create your own copy of the project.
    + [Clone](https://github.com/git-guides/git-clone) the project to your local computer

    ```shell
    # Replace <you-github-username> with your Github User Name otherwise
    # you will not be able to clone from the fork you created earlier.
    git clone https://github.com/<your-github-username>/schemachange.git
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
    git checkout master
    git pull upstream master --tags
    ```

2. Create and Activate a Virtual Environment

    1. From the repo directory, create a virtual environment
       ```bash
       python -m venv .venv
       ```

    2. Activate your virtual environment. The following table is a replication
       of [this](https://docs.python.org/3/library/venv.html#how-venvs-work) table:

       | Platform | Shell      | Command                               |
       |----------|------------|---------------------------------------|
       | POSIX    | bash/zsh   | `$ source <venv>/bin/activate`        |
       | POSIX    | fish       | `$ source <venv>/bin/activate.fish`   |
       | POSIX    | csh/tcsh   | `$ source <venv>/bin/activate.csh`    |
       | POSIX    | PowerShell | `$ <venv>/bin/Activate.ps1`           |
       | Windows  | cmd.exe    | `C:\> <venv>\Scripts\activate.bat`    |
       | Windows  | PowerShell | `PS C:\> <venv>\Scripts\Activate.ps1` |

    3. With your virtual environment activated, upgrade `pip`

       ```bash
       python -m pip install --upgrade pip
       ```

    4. Install the repo as an "editable" package with development dependencies

       ```bash
       pip install -e .[dev]
       ```

3. Develop your contribution
    + Create a branch for the features you want to work on. Since the branch name will appear in the merge message, use
      a sensible name such as 'update-build-library-dependencies':

      ```shell
      git checkout -b update-build-library-dependencies
      ```

    + Commit locally as you progress ( [git add](https://github.com/git-guides/git-add)
      and [git commit](https://github.com/git-guides/git-commit) ). Use a properly formatted commit message. Be sure to
      document any changed behavior in the [CHANGELOG.md](../CHANGELOG.md) file to help us collate the changes for a specific release.

4. Test your contribution locally

   ```bash
   python -m pytest
   ```
   PS: Please add test cases to the features you are developing so that over time, we can capture any lapse in functionality changes.

5. Perform integration tests on your branch from your fork
    - Follow the [provisioning and schemachange setup instructions](../demo/README.MD) to configure your Snowflake account for testing.
    - Follow [these](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow)
   instructions to manually run the `master-pytest` workflow on your fork of the repo, targeting your feature branch.

6. Push your contribution to GitHub

   [Push](https://github.com/git-guides/git-push) your changes back to your fork on GitHub

    ```shell
    git push origin update-build-library-dependencies
    ```

7. Raise a Pull Request to merge your contribution into the a Schemachange Release
    + Go to GitHub. The new branch will show up with a
      green [Pull Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#initiating-the-pull-request)
      button. Make sure the title and message are clear, concise and self-explanatory. Then click the button to submit
      it.
