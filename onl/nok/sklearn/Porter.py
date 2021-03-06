import os
import argparse

import sklearn
from sklearn.ensemble import weight_boosting

from classifier.Classifier import Classifier
from classifier.DecisionTreeClassifier import DecisionTreeClassifier
from classifier.AdaBoostClassifier import AdaBoostClassifier


def port(model, language="java", method_name='predict', class_name='Tmp'):
    """Port a trained model in the syntax of a specific programming language.

    Parameters
    ----------
    :param to : String (default='java')
        The required syntax (e.g. 'java', 'c' or 'js' (or 'javascript')).

    :param model : Model object
        An instance of a trained model (e.g. DecisionTreeClassifier()).

    :param method_name : String (default='predict')
        The name of the prediction method.

    :param class_name : String (default='Tmp')
        The name of the environment class.
    """

    md_type, md_name = get_model_data(model)
    md_path = '.'.join([md_type, md_name])

    md_mod = __import__(md_path, globals(), locals(), [md_name], -1)
    klass = getattr(md_mod, md_name)
    instance = klass(language=language, method_name=method_name, class_name=class_name)
    return instance.port(model)


def get_model_data(model):
    """Get data of the assigned model.

    Parameters
    ----------
    :param model : Model object
        An instance of a trained model (e.g. DecisionTreeClassifier()).

    :return md_type : String ['regressor', 'classifier']
        The model type.

    :return md_name : String
        The name of the used algorithm.
    """

    md_type = is_convertible_model(model)
    md_name = type(model).__name__
    return md_type, md_name


def get_classifiers():
    '''Get a list of convertible classifiers.'''

    return [
        sklearn.tree.tree.DecisionTreeClassifier,
        sklearn.ensemble.AdaBoostClassifier
    ]


def get_regressors():
    '''Get a list of all convertible regressors.'''
    return []


def is_convertible_model(model):
    """Check whether the model is a convertible classifier or regressor.

    Parameters
    ----------
    :param model : Model object
        An instance of a trained model (e.g. DecisionTreeClassifier()).

    See also
    --------
    onl.nok.sklearn.classifier.*, onl.nok.sklearn.regressor.*
    """

    if type(model) in get_classifiers():
        return 'classifier'

    if type(model) in get_regressors():
        return 'regressors'

    raise ValueError('The model is not an instance of a supported classifier or regressor.')


def main():
    parser = argparse.ArgumentParser(
        description='Port trained scikit-learn models to a low-level programming language.',
        epilog='More details on https://github.com/nok/sklearn-porter')
    parser.add_argument(
        'FILE',
        help='set the classifier in pickle format')
    parser.add_argument(
        '--to',
        choices=['c', 'java', 'js'],
        default='java',
        required=False,
        help='set target programming language')
    parser.add_argument(
        '--output',
        type=str,
        required=False,
        help='set the output path')

    args = vars(parser.parse_args())

    input_file = str(args['FILE'])
    if input_file.endswith('.pkl') and os.path.isfile(input_file):

        # Target programming language:
        lang = str(args['to']) if str(args['to']) is not '' else 'java'

        # Input and output filename:
        inn = str(args['FILE'])
        out = inn.split('.')[-2] + '.' + lang

        if str(args['output']).endswith(('.c', '.java', '.js')):
            out = str(args['output'])
            lang = out.split('.')[-1].lower()

        from sklearn.externals import joblib
        with open(out, 'w') as file:
            model = joblib.load(inn)
            # class_name = out.split('.')[-2].lower().title()
            file.write(port(model))


if __name__ == "__main__":
    main()
